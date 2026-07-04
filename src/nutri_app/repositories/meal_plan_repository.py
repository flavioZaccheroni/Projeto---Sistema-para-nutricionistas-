from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.meal_plan import Meal, MealPlan, MealPlanItem
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class MealPlanRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, plan: MealPlan) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO planos_alimentares (
                    paciente_id, consulta_id, data_inicio, data_fim, objetivo,
                    energia_alvo_kcal, proteina_alvo_g, carboidrato_alvo_g, lipidios_alvo_g,
                    energia_total_kcal, proteina_total_g, carboidrato_total_g,
                    lipidios_total_g, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._plan_values(plan),
            )
            plan_id = int(cursor.lastrowid)
            self._insert_meals(connection, plan_id, plan.meals)
            return plan_id

    def update(self, plan: MealPlan) -> None:
        if plan.id is None:
            raise ValueError("Plano alimentar sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE planos_alimentares
                SET paciente_id = ?,
                    consulta_id = ?,
                    data_inicio = ?,
                    data_fim = ?,
                    objetivo = ?,
                    energia_alvo_kcal = ?,
                    proteina_alvo_g = ?,
                    carboidrato_alvo_g = ?,
                    lipidios_alvo_g = ?,
                    energia_total_kcal = ?,
                    proteina_total_g = ?,
                    carboidrato_total_g = ?,
                    lipidios_total_g = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._plan_values(plan), plan.id),
            )
            self._soft_delete_children(connection, plan.id)
            self._insert_meals(connection, plan.id, plan.meals)

    def soft_delete(self, plan_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE planos_alimentares
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (plan_id,),
            )
            self._soft_delete_children(connection, plan_id)

    def get(self, plan_id: int) -> MealPlan | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE pa.id = ? AND pa.deleted_at IS NULL AND p.deleted_at IS NULL
                """,
                (plan_id,),
            ).fetchone()
            if row is None:
                return None
            meal_rows = connection.execute(
                """
                SELECT id, nome, horario, observacoes, created_at, updated_at
                FROM plano_refeicoes
                WHERE plano_id = ? AND deleted_at IS NULL
                ORDER BY id
                """,
                (plan_id,),
            ).fetchall()
            meals = [self._row_to_meal(connection, meal_row) for meal_row in meal_rows]
        return self._row_to_plan(row, meals)

    def list_active(self, patient_query: str = "") -> list[MealPlan]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE pa.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY pa.data_inicio DESC, pa.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_plan(row, []) for row in rows]

    def _plan_values(self, plan: MealPlan) -> tuple:
        return (
            plan.patient_id,
            plan.appointment_id,
            plan.start_date.isoformat(),
            plan.end_date.isoformat() if plan.end_date is not None else None,
            plan.objective,
            plan.target_energy_kcal,
            plan.target_protein_g,
            plan.target_carbohydrate_g,
            plan.target_fat_g,
            plan.total_energy_kcal,
            plan.total_protein_g,
            plan.total_carbohydrate_g,
            plan.total_fat_g,
            plan.notes,
        )

    def _insert_meals(self, connection, plan_id: int, meals: list[Meal]) -> None:
        for meal in meals:
            cursor = connection.execute(
                """
                INSERT INTO plano_refeicoes (plano_id, nome, horario, observacoes)
                VALUES (?, ?, ?, ?)
                """,
                (plan_id, meal.name, meal.time, meal.notes),
            )
            meal_id = int(cursor.lastrowid)
            for item in meal.items:
                connection.execute(
                    """
                    INSERT INTO plano_itens (
                        refeicao_id, alimento, quantidade, unidade, energia_kcal,
                        proteina_g, carboidrato_g, lipidios_g, substituicoes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meal_id,
                        item.food,
                        item.quantity,
                        item.unit,
                        item.energy_kcal,
                        item.protein_g,
                        item.carbohydrate_g,
                        item.fat_g,
                        item.substitutions,
                    ),
                )

    def _soft_delete_children(self, connection, plan_id: int) -> None:
        connection.execute(
            """
            UPDATE plano_itens
            SET deleted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE refeicao_id IN (
                SELECT id FROM plano_refeicoes WHERE plano_id = ?
            ) AND deleted_at IS NULL
            """,
            (plan_id,),
        )
        connection.execute(
            """
            UPDATE plano_refeicoes
            SET deleted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE plano_id = ? AND deleted_at IS NULL
            """,
            (plan_id,),
        )

    def _select_sql(self) -> str:
        return """
            SELECT pa.id, pa.paciente_id, p.nome AS paciente_nome, pa.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   pa.data_inicio, pa.data_fim, pa.objetivo, pa.energia_alvo_kcal,
                   pa.proteina_alvo_g, pa.carboidrato_alvo_g, pa.lipidios_alvo_g,
                   pa.energia_total_kcal, pa.proteina_total_g, pa.carboidrato_total_g,
                   pa.lipidios_total_g, pa.observacoes, pa.created_at, pa.updated_at
            FROM planos_alimentares pa
            JOIN pacientes p ON p.id = pa.paciente_id
            LEFT JOIN consultas c ON c.id = pa.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_meal(self, connection, row) -> Meal:
        item_rows = connection.execute(
            """
            SELECT id, alimento, quantidade, unidade, energia_kcal, proteina_g,
                   carboidrato_g, lipidios_g, substituicoes, created_at, updated_at
            FROM plano_itens
            WHERE refeicao_id = ? AND deleted_at IS NULL
            ORDER BY id
            """,
            (row["id"],),
        ).fetchall()
        return Meal(
            id=row["id"],
            name=row["nome"],
            time=row["horario"] or "",
            notes=row["observacoes"] or "",
            items=[self._row_to_item(item_row) for item_row in item_rows],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_item(self, row) -> MealPlanItem:
        return MealPlanItem(
            id=row["id"],
            food=row["alimento"],
            quantity=float(row["quantidade"]),
            unit=row["unidade"],
            energy_kcal=float(row["energia_kcal"]),
            protein_g=float(row["proteina_g"]),
            carbohydrate_g=float(row["carboidrato_g"]),
            fat_g=float(row["lipidios_g"]),
            substitutions=row["substituicoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_plan(self, row, meals: list[Meal]) -> MealPlan:
        return MealPlan(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            start_date=date.fromisoformat(row["data_inicio"]),
            end_date=date.fromisoformat(row["data_fim"]) if row["data_fim"] else None,
            objective=row["objetivo"],
            target_energy_kcal=self._optional_float(row["energia_alvo_kcal"]),
            target_protein_g=self._optional_float(row["proteina_alvo_g"]),
            target_carbohydrate_g=self._optional_float(row["carboidrato_alvo_g"]),
            target_fat_g=self._optional_float(row["lipidios_alvo_g"]),
            total_energy_kcal=float(row["energia_total_kcal"]),
            total_protein_g=float(row["proteina_total_g"]),
            total_carbohydrate_g=float(row["carboidrato_total_g"]),
            total_fat_g=float(row["lipidios_total_g"]),
            notes=row["observacoes"] or "",
            meals=meals,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _optional_float(self, value) -> float | None:
        return float(value) if value is not None else None
