from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.laboratory_exam import LaboratoryExam, LaboratoryExamItem
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class LaboratoryExamRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, exam: LaboratoryExam) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO exames_laboratoriais (
                    paciente_id, consulta_id, data_exame, laboratorio, observacoes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                self._exam_values(exam),
            )
            exam_id = int(cursor.lastrowid)
            self._insert_items(connection, exam_id, exam.items)
            return exam_id

    def update(self, exam: LaboratoryExam) -> None:
        if exam.id is None:
            raise ValueError("Exame laboratorial sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE exames_laboratoriais
                SET paciente_id = ?,
                    consulta_id = ?,
                    data_exame = ?,
                    laboratorio = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._exam_values(exam), exam.id),
            )
            connection.execute(
                """
                UPDATE exame_itens
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE exame_id = ? AND deleted_at IS NULL
                """,
                (exam.id,),
            )
            self._insert_items(connection, exam.id, exam.items)

    def soft_delete(self, exam_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE exames_laboratoriais
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (exam_id,),
            )
            connection.execute(
                """
                UPDATE exame_itens
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE exame_id = ? AND deleted_at IS NULL
                """,
                (exam_id,),
            )

    def get(self, exam_id: int) -> LaboratoryExam | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE e.id = ? AND e.deleted_at IS NULL AND p.deleted_at IS NULL
                {self._group_sql()}
                """,
                (exam_id,),
            ).fetchone()
            if row is None:
                return None
            item_rows = self._select_items(connection, exam_id)
        return self._row_to_exam(row, item_rows)

    def list_active(self, patient_query: str = "") -> list[LaboratoryExam]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE e.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                {self._group_sql()}
                ORDER BY e.data_exame DESC, e.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_exam(row, []) for row in rows]

    def _exam_values(self, exam: LaboratoryExam) -> tuple:
        return (
            exam.patient_id,
            exam.appointment_id,
            exam.exam_date.isoformat(),
            exam.laboratory,
            exam.notes,
        )

    def _insert_items(self, connection, exam_id: int, items: list[LaboratoryExamItem]) -> None:
        for item in items:
            connection.execute(
                """
                INSERT INTO exame_itens (exame_id, nome, valor, unidade, referencia, alerta)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    exam_id,
                    item.name,
                    item.value,
                    item.unit,
                    item.reference,
                    item.alert,
                ),
            )

    def _select_items(self, connection, exam_id: int) -> list:
        return connection.execute(
            """
            SELECT id, nome, valor, unidade, referencia, alerta, created_at, updated_at
            FROM exame_itens
            WHERE exame_id = ? AND deleted_at IS NULL
            ORDER BY id
            """,
            (exam_id,),
        ).fetchall()

    def _select_sql(self) -> str:
        return """
            SELECT e.id, e.paciente_id, p.nome AS paciente_nome, e.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   e.data_exame, e.laboratorio, e.observacoes, e.created_at, e.updated_at,
                   COUNT(i.id) AS total_itens,
                   SUM(CASE WHEN i.alerta IS NOT NULL AND trim(i.alerta) <> '' THEN 1 ELSE 0 END)
                       AS total_alertas
            FROM exames_laboratoriais e
            JOIN pacientes p ON p.id = e.paciente_id
            LEFT JOIN consultas c ON c.id = e.consulta_id AND c.deleted_at IS NULL
            LEFT JOIN exame_itens i ON i.exame_id = e.id AND i.deleted_at IS NULL
        """

    def _group_sql(self) -> str:
        return """
            GROUP BY e.id, e.paciente_id, p.nome, e.consulta_id, c.id, c.data_hora, c.tipo,
                     e.data_exame, e.laboratorio, e.observacoes, e.created_at, e.updated_at
        """

    def _row_to_exam(self, row, item_rows: list) -> LaboratoryExam:
        return LaboratoryExam(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            exam_date=date.fromisoformat(row["data_exame"]),
            laboratory=row["laboratorio"] or "",
            notes=row["observacoes"] or "",
            items=[self._row_to_item(item_row) for item_row in item_rows],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_item(self, row) -> LaboratoryExamItem:
        return LaboratoryExamItem(
            id=row["id"],
            name=row["nome"],
            value=float(row["valor"]) if row["valor"] is not None else None,
            unit=row["unidade"] or "",
            reference=row["referencia"] or "",
            alert=row["alerta"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
