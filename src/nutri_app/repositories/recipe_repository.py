from __future__ import annotations

from datetime import datetime

from nutri_app.domain.recipe import Recipe, RecipeIngredient
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class RecipeRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, recipe: Recipe) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO receitas (
                    nome, categoria, rendimento_porcoes, peso_total_g, modo_preparo,
                    foto_caminho, energia_total_kcal, proteina_total_g,
                    carboidrato_total_g, lipidios_total_g, fibras_total_g,
                    sodio_total_mg, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._recipe_values(recipe),
            )
            recipe_id = int(cursor.lastrowid)
            self._insert_ingredients(connection, recipe_id, recipe.ingredients)
            return recipe_id

    def update(self, recipe: Recipe) -> None:
        if recipe.id is None:
            raise ValueError("Receita sem ID nao pode ser atualizada.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE receitas
                SET nome = ?,
                    categoria = ?,
                    rendimento_porcoes = ?,
                    peso_total_g = ?,
                    modo_preparo = ?,
                    foto_caminho = ?,
                    energia_total_kcal = ?,
                    proteina_total_g = ?,
                    carboidrato_total_g = ?,
                    lipidios_total_g = ?,
                    fibras_total_g = ?,
                    sodio_total_mg = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._recipe_values(recipe), recipe.id),
            )
            self._soft_delete_ingredients(connection, recipe.id)
            self._insert_ingredients(connection, recipe.id, recipe.ingredients)

    def soft_delete(self, recipe_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE receitas
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (recipe_id,),
            )
            self._soft_delete_ingredients(connection, recipe_id)

    def get(self, recipe_id: int) -> Recipe | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"{self._select_sql()} WHERE id = ? AND deleted_at IS NULL",
                (recipe_id,),
            ).fetchone()
            if row is None:
                return None
            ingredient_rows = self._select_ingredients(connection, recipe_id)
        return self._row_to_recipe(row, [self._row_to_ingredient(item) for item in ingredient_rows])

    def list_active(self, query: str = "") -> list[Recipe]:
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
                  )
                ORDER BY nome
                """,
                (normalized, normalized, normalized),
            ).fetchall()
        return [self._row_to_recipe(row, []) for row in rows]

    def _recipe_values(self, recipe: Recipe) -> tuple:
        return (
            recipe.name,
            recipe.category,
            recipe.servings,
            recipe.total_weight_g,
            recipe.preparation_method,
            recipe.photo_path,
            recipe.total_energy_kcal,
            recipe.total_protein_g,
            recipe.total_carbohydrate_g,
            recipe.total_fat_g,
            recipe.total_fiber_g,
            recipe.total_sodium_mg,
            recipe.notes,
        )

    def _insert_ingredients(
        self,
        connection,
        recipe_id: int,
        ingredients: list[RecipeIngredient],
    ) -> None:
        for ingredient in ingredients:
            connection.execute(
                """
                INSERT INTO receita_ingredientes (
                    receita_id, alimento_id, nome, quantidade, unidade, peso_g,
                    energia_kcal, proteina_g, carboidrato_g, lipidios_g,
                    fibras_g, sodio_mg, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recipe_id,
                    ingredient.food_id,
                    ingredient.name,
                    ingredient.quantity,
                    ingredient.unit,
                    ingredient.weight_g,
                    ingredient.energy_kcal,
                    ingredient.protein_g,
                    ingredient.carbohydrate_g,
                    ingredient.fat_g,
                    ingredient.fiber_g,
                    ingredient.sodium_mg,
                    ingredient.notes,
                ),
            )

    def _soft_delete_ingredients(self, connection, recipe_id: int) -> None:
        connection.execute(
            """
            UPDATE receita_ingredientes
            SET deleted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE receita_id = ? AND deleted_at IS NULL
            """,
            (recipe_id,),
        )

    def _select_ingredients(self, connection, recipe_id: int) -> list:
        return connection.execute(
            """
            SELECT id, alimento_id, nome, quantidade, unidade, peso_g, energia_kcal,
                   proteina_g, carboidrato_g, lipidios_g, fibras_g, sodio_mg,
                   observacoes, created_at, updated_at
            FROM receita_ingredientes
            WHERE receita_id = ? AND deleted_at IS NULL
            ORDER BY id
            """,
            (recipe_id,),
        ).fetchall()

    def _select_sql(self) -> str:
        return """
            SELECT id, nome, categoria, rendimento_porcoes, peso_total_g,
                   modo_preparo, foto_caminho, energia_total_kcal, proteina_total_g,
                   carboidrato_total_g, lipidios_total_g, fibras_total_g,
                   sodio_total_mg, observacoes, created_at, updated_at
            FROM receitas
        """

    def _row_to_recipe(self, row, ingredients: list[RecipeIngredient]) -> Recipe:
        return Recipe(
            id=row["id"],
            name=row["nome"],
            category=row["categoria"] or "",
            servings=float(row["rendimento_porcoes"]),
            total_weight_g=float(row["peso_total_g"]),
            preparation_method=row["modo_preparo"] or "",
            photo_path=row["foto_caminho"] or "",
            total_energy_kcal=float(row["energia_total_kcal"]),
            total_protein_g=float(row["proteina_total_g"]),
            total_carbohydrate_g=float(row["carboidrato_total_g"]),
            total_fat_g=float(row["lipidios_total_g"]),
            total_fiber_g=float(row["fibras_total_g"]),
            total_sodium_mg=float(row["sodio_total_mg"]),
            notes=row["observacoes"] or "",
            ingredients=ingredients,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_ingredient(self, row) -> RecipeIngredient:
        return RecipeIngredient(
            id=row["id"],
            food_id=row["alimento_id"],
            name=row["nome"],
            quantity=float(row["quantidade"]),
            unit=row["unidade"],
            weight_g=float(row["peso_g"]),
            energy_kcal=float(row["energia_kcal"]),
            protein_g=float(row["proteina_g"]),
            carbohydrate_g=float(row["carboidrato_g"]),
            fat_g=float(row["lipidios_g"]),
            fiber_g=float(row["fibras_g"]),
            sodium_mg=float(row["sodio_mg"]),
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
