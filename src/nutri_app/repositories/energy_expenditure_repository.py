from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.energy_expenditure import (
    BiologicalSex,
    EnergyEquation,
    EnergyExpenditure,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class EnergyExpenditureRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, expenditure: EnergyExpenditure) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO gastos_energeticos (
                    paciente_id, consulta_id, data_avaliacao, sexo, idade_anos,
                    peso_kg, altura_cm, massa_magra_kg, equacao, fator_atividade,
                    fator_estresse, ajuste_objetivo_kcal, tmb_kcal, get_kcal,
                    proteina_g, carboidrato_g, lipidios_g, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(expenditure),
            )
            return int(cursor.lastrowid)

    def update(self, expenditure: EnergyExpenditure) -> None:
        if expenditure.id is None:
            raise ValueError("Gasto energetico sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE gastos_energeticos
                SET paciente_id = ?,
                    consulta_id = ?,
                    data_avaliacao = ?,
                    sexo = ?,
                    idade_anos = ?,
                    peso_kg = ?,
                    altura_cm = ?,
                    massa_magra_kg = ?,
                    equacao = ?,
                    fator_atividade = ?,
                    fator_estresse = ?,
                    ajuste_objetivo_kcal = ?,
                    tmb_kcal = ?,
                    get_kcal = ?,
                    proteina_g = ?,
                    carboidrato_g = ?,
                    lipidios_g = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(expenditure), expenditure.id),
            )

    def soft_delete(self, expenditure_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE gastos_energeticos
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (expenditure_id,),
            )

    def get(self, expenditure_id: int) -> EnergyExpenditure | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE ge.id = ? AND ge.deleted_at IS NULL AND p.deleted_at IS NULL
                """,
                (expenditure_id,),
            ).fetchone()
        return self._row_to_expenditure(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[EnergyExpenditure]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE ge.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY ge.data_avaliacao DESC, ge.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_expenditure(row) for row in rows]

    def _values(self, expenditure: EnergyExpenditure) -> tuple:
        return (
            expenditure.patient_id,
            expenditure.appointment_id,
            expenditure.assessment_date.isoformat(),
            expenditure.sex.value,
            expenditure.age_years,
            expenditure.weight_kg,
            expenditure.height_cm,
            expenditure.lean_mass_kg,
            expenditure.equation.value,
            expenditure.activity_factor,
            expenditure.stress_factor,
            expenditure.goal_adjustment_kcal,
            expenditure.basal_energy_kcal,
            expenditure.total_energy_kcal,
            expenditure.protein_g,
            expenditure.carbohydrate_g,
            expenditure.fat_g,
            expenditure.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT ge.id, ge.paciente_id, p.nome AS paciente_nome, ge.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   ge.data_avaliacao, ge.sexo, ge.idade_anos, ge.peso_kg,
                   ge.altura_cm, ge.massa_magra_kg, ge.equacao, ge.fator_atividade,
                   ge.fator_estresse, ge.ajuste_objetivo_kcal, ge.tmb_kcal,
                   ge.get_kcal, ge.proteina_g, ge.carboidrato_g, ge.lipidios_g,
                   ge.observacoes, ge.created_at, ge.updated_at
            FROM gastos_energeticos ge
            JOIN pacientes p ON p.id = ge.paciente_id
            LEFT JOIN consultas c ON c.id = ge.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_expenditure(self, row) -> EnergyExpenditure:
        return EnergyExpenditure(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            assessment_date=date.fromisoformat(row["data_avaliacao"]),
            sex=BiologicalSex(row["sexo"]),
            age_years=int(row["idade_anos"]),
            weight_kg=float(row["peso_kg"]),
            height_cm=float(row["altura_cm"]),
            lean_mass_kg=float(row["massa_magra_kg"])
            if row["massa_magra_kg"] is not None
            else None,
            equation=EnergyEquation(row["equacao"]),
            activity_factor=float(row["fator_atividade"]),
            stress_factor=float(row["fator_estresse"]),
            goal_adjustment_kcal=float(row["ajuste_objetivo_kcal"]),
            basal_energy_kcal=float(row["tmb_kcal"]),
            total_energy_kcal=float(row["get_kcal"]),
            protein_g=float(row["proteina_g"]),
            carbohydrate_g=float(row["carboidrato_g"]),
            fat_g=float(row["lipidios_g"]),
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
