from __future__ import annotations

from datetime import datetime

from nutri_app.domain.report import ClinicalReport
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class ClinicalReportRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, report: ClinicalReport) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO relatorios (
                    paciente_id, tipo, titulo, caminho_arquivo, parametros, conteudo, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.patient_id,
                    report.report_type,
                    report.title,
                    report.file_path,
                    report.parameters,
                    report.content,
                    report.status,
                ),
            )
            return int(cursor.lastrowid)

    def get(self, report_id: int) -> ClinicalReport | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE r.id = ? AND r.deleted_at IS NULL
                """,
                (report_id,),
            ).fetchone()
        return self._row_to_report(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[ClinicalReport]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE r.deleted_at IS NULL
                  AND (? = '%%' OR lower(coalesce(p.nome, '')) LIKE ?)
                ORDER BY r.created_at DESC, r.id DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_report(row) for row in rows]

    def build_clinical_context(self, patient_id: int) -> dict[str, object]:
        with self.connection_factory.connect() as connection:
            context = {
                "anamnesis": self._fetch_one(
                    connection,
                    """
                    SELECT queixa_principal, historia_doenca_atual, rotina_alimentar,
                           sintomas_gastrointestinais, observacoes
                    FROM anamnese
                    WHERE paciente_id = ? AND deleted_at IS NULL
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT 1
                    """,
                    patient_id,
                ),
                "anthropometry": self._fetch_one(
                    connection,
                    """
                    SELECT data_avaliacao, peso_kg, altura_m, imc, classificacao_imc
                    FROM antropometrias
                    WHERE paciente_id = ? AND deleted_at IS NULL
                    ORDER BY data_avaliacao DESC, updated_at DESC
                    LIMIT 1
                    """,
                    patient_id,
                ),
                "energy_expenditure": self._fetch_one(
                    connection,
                    """
                    SELECT equacao, tmb_kcal, get_kcal, proteina_g, carboidrato_g,
                           lipidios_g
                    FROM gastos_energeticos
                    WHERE paciente_id = ? AND deleted_at IS NULL
                    ORDER BY data_avaliacao DESC, updated_at DESC
                    LIMIT 1
                    """,
                    patient_id,
                ),
                "laboratory_exam": self._latest_laboratory_exam(connection, patient_id),
                "diagnosis": self._fetch_one(
                    connection,
                    """
                    SELECT classificacao, gravidade, criterios, conduta, observacoes
                    FROM diagnosticos_nutricionais
                    WHERE paciente_id = ? AND deleted_at IS NULL
                    ORDER BY data_diagnostico DESC, updated_at DESC
                    LIMIT 1
                    """,
                    patient_id,
                ),
                "meal_plan": self._latest_meal_plan(connection, patient_id),
            }
        return context

    def _latest_laboratory_exam(self, connection, patient_id: int) -> dict:
        exam = self._fetch_one(
            connection,
            """
            SELECT id, data_exame, laboratorio, observacoes
            FROM exames_laboratoriais
            WHERE paciente_id = ? AND deleted_at IS NULL
            ORDER BY data_exame DESC, updated_at DESC
            LIMIT 1
            """,
            patient_id,
        )
        if not exam:
            return {}
        rows = connection.execute(
            """
            SELECT nome, valor, unidade, referencia, alerta
            FROM exame_itens
            WHERE exame_id = ? AND deleted_at IS NULL
            ORDER BY id
            """,
            (exam["id"],),
        ).fetchall()
        exam["itens"] = [dict(row) for row in rows]
        return exam

    def _latest_meal_plan(self, connection, patient_id: int) -> dict:
        plan = self._fetch_one(
            connection,
            """
            SELECT id, objetivo, energia_total_kcal, proteina_total_g,
                   carboidrato_total_g, lipidios_total_g, observacoes
            FROM planos_alimentares
            WHERE paciente_id = ? AND deleted_at IS NULL
            ORDER BY data_inicio DESC, updated_at DESC
            LIMIT 1
            """,
            patient_id,
        )
        if not plan:
            return {}
        meal_rows = connection.execute(
            """
            SELECT id, nome, horario, observacoes
            FROM plano_refeicoes
            WHERE plano_id = ? AND deleted_at IS NULL
            ORDER BY id
            """,
            (plan["id"],),
        ).fetchall()
        meals = []
        for meal_row in meal_rows:
            meal = dict(meal_row)
            item_rows = connection.execute(
                """
                SELECT alimento, quantidade, unidade, energia_kcal
                FROM plano_itens
                WHERE refeicao_id = ? AND deleted_at IS NULL
                ORDER BY id
                """,
                (meal["id"],),
            ).fetchall()
            meal["itens"] = [dict(row) for row in item_rows]
            meals.append(meal)
        plan["refeicoes"] = meals
        return plan

    def _fetch_one(self, connection, sql: str, patient_id: int) -> dict:
        row = connection.execute(sql, (patient_id,)).fetchone()
        return dict(row) if row is not None else {}

    def _select_sql(self) -> str:
        return """
            SELECT r.id, r.paciente_id, p.nome AS paciente_nome, r.tipo, r.titulo,
                   r.caminho_arquivo, r.parametros, r.conteudo, r.status,
                   r.created_at, r.updated_at
            FROM relatorios r
            LEFT JOIN pacientes p ON p.id = r.paciente_id
        """

    def _row_to_report(self, row) -> ClinicalReport:
        return ClinicalReport(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"] or "",
            report_type=row["tipo"],
            title=row["titulo"] or row["tipo"],
            file_path=row["caminho_arquivo"] or "",
            parameters=row["parametros"] or "",
            content=row["conteudo"] or "",
            status=row["status"] or "Gerado",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
