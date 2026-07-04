from __future__ import annotations

from datetime import datetime

from nutri_app.domain.food import Food, FoodSource
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class FoodRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, food: Food) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO alimentos (
                    nome, categoria, fonte, porcao_base_g, medida_caseira, energia_kcal,
                    proteina_g, carboidrato_g, lipidios_g, fibras_g, sodio_mg,
                    indice_glicemico, micronutrientes, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(food),
            )
            return int(cursor.lastrowid)

    def update(self, food: Food) -> None:
        if food.id is None:
            raise ValueError("Alimento sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE alimentos
                SET nome = ?,
                    categoria = ?,
                    fonte = ?,
                    porcao_base_g = ?,
                    medida_caseira = ?,
                    energia_kcal = ?,
                    proteina_g = ?,
                    carboidrato_g = ?,
                    lipidios_g = ?,
                    fibras_g = ?,
                    sodio_mg = ?,
                    indice_glicemico = ?,
                    micronutrientes = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(food), food.id),
            )

    def soft_delete(self, food_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE alimentos
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (food_id,),
            )

    def get(self, food_id: int) -> Food | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"{self._select_sql()} WHERE id = ? AND deleted_at IS NULL",
                (food_id,),
            ).fetchone()
        return self._row_to_food(row) if row is not None else None

    def list_active(self, query: str = "") -> list[Food]:
        normalized = f"%{query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE deleted_at IS NULL
                  AND (
                    ? = '%%'
                    OR lower(nome) LIKE ?
                    OR lower(coalesce(categoria, '')) LIKE ?
                    OR lower(fonte) LIKE ?
                  )
                ORDER BY nome
                """,
                (normalized, normalized, normalized, normalized),
            ).fetchall()
        return [self._row_to_food(row) for row in rows]

    def _values(self, food: Food) -> tuple:
        return (
            food.name,
            food.category,
            food.source.value,
            food.base_portion_g,
            food.household_measure,
            food.energy_kcal,
            food.protein_g,
            food.carbohydrate_g,
            food.fat_g,
            food.fiber_g,
            food.sodium_mg,
            food.glycemic_index,
            food.micronutrients,
            food.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT id, nome, categoria, fonte, porcao_base_g, medida_caseira,
                   energia_kcal, proteina_g, carboidrato_g, lipidios_g,
                   fibras_g, sodio_mg, indice_glicemico, micronutrientes,
                   observacoes, created_at, updated_at
            FROM alimentos
        """

    def _row_to_food(self, row) -> Food:
        return Food(
            id=row["id"],
            name=row["nome"],
            category=row["categoria"] or "",
            source=FoodSource(row["fonte"]),
            base_portion_g=float(row["porcao_base_g"]),
            household_measure=row["medida_caseira"] or "",
            energy_kcal=float(row["energia_kcal"]),
            protein_g=float(row["proteina_g"]),
            carbohydrate_g=float(row["carboidrato_g"]),
            fat_g=float(row["lipidios_g"]),
            fiber_g=float(row["fibras_g"]),
            sodium_mg=float(row["sodio_mg"]),
            glycemic_index=float(row["indice_glicemico"])
            if row["indice_glicemico"] is not None
            else None,
            micronutrients=row["micronutrientes"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
