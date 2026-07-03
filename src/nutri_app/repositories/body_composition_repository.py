from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.body_composition import BodyComposition, BodyCompositionProtocol
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class BodyCompositionRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, composition: BodyComposition) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO composicoes_corporais (
                    paciente_id, consulta_id, data_avaliacao, protocolo, peso_kg,
                    percentual_gordura, massa_gorda_kg, massa_magra_kg,
                    agua_corporal_percentual, massa_muscular_kg, gordura_visceral,
                    observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(composition),
            )
            return int(cursor.lastrowid)

    def update(self, composition: BodyComposition) -> None:
        if composition.id is None:
            raise ValueError("Composicao corporal sem ID nao pode ser atualizada.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE composicoes_corporais
                SET paciente_id = ?,
                    consulta_id = ?,
                    data_avaliacao = ?,
                    protocolo = ?,
                    peso_kg = ?,
                    percentual_gordura = ?,
                    massa_gorda_kg = ?,
                    massa_magra_kg = ?,
                    agua_corporal_percentual = ?,
                    massa_muscular_kg = ?,
                    gordura_visceral = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(composition), composition.id),
            )

    def soft_delete(self, composition_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE composicoes_corporais
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (composition_id,),
            )

    def get(self, composition_id: int) -> BodyComposition | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE cc.id = ? AND cc.deleted_at IS NULL AND p.deleted_at IS NULL
                """,
                (composition_id,),
            ).fetchone()
        return self._row_to_composition(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[BodyComposition]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE cc.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY cc.data_avaliacao DESC, cc.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_composition(row) for row in rows]

    def _values(self, composition: BodyComposition) -> tuple:
        return (
            composition.patient_id,
            composition.appointment_id,
            composition.assessment_date.isoformat(),
            composition.protocol.value,
            composition.weight_kg,
            composition.body_fat_percentage,
            composition.fat_mass_kg,
            composition.lean_mass_kg,
            composition.body_water_percentage,
            composition.muscle_mass_kg,
            composition.visceral_fat,
            composition.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT cc.id, cc.paciente_id, p.nome AS paciente_nome, cc.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   cc.data_avaliacao, cc.protocolo, cc.peso_kg,
                   cc.percentual_gordura, cc.massa_gorda_kg, cc.massa_magra_kg,
                   cc.agua_corporal_percentual, cc.massa_muscular_kg,
                   cc.gordura_visceral, cc.observacoes, cc.created_at, cc.updated_at
            FROM composicoes_corporais cc
            JOIN pacientes p ON p.id = cc.paciente_id
            LEFT JOIN consultas c ON c.id = cc.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_composition(self, row) -> BodyComposition:
        return BodyComposition(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            assessment_date=date.fromisoformat(row["data_avaliacao"]),
            protocol=BodyCompositionProtocol(row["protocolo"]),
            weight_kg=float(row["peso_kg"]),
            body_fat_percentage=float(row["percentual_gordura"]),
            fat_mass_kg=float(row["massa_gorda_kg"]),
            lean_mass_kg=float(row["massa_magra_kg"]),
            body_water_percentage=float(row["agua_corporal_percentual"])
            if row["agua_corporal_percentual"] is not None
            else None,
            muscle_mass_kg=float(row["massa_muscular_kg"])
            if row["massa_muscular_kg"] is not None
            else None,
            visceral_fat=float(row["gordura_visceral"])
            if row["gordura_visceral"] is not None
            else None,
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
