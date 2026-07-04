from __future__ import annotations

from dataclasses import dataclass

from nutri_app.domain.recipe import Recipe, RecipeIngredient


@dataclass(frozen=True)
class RecipeNutrients:
    energy_kcal: float
    protein_g: float
    carbohydrate_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float


class RecipeService:
    def validate_recipe(self, recipe: Recipe) -> None:
        if not recipe.name.strip():
            raise ValueError("Nome da receita deve ser informado.")
        if recipe.servings <= 0:
            raise ValueError("Rendimento deve ser maior que zero.")
        if recipe.total_weight_g <= 0:
            raise ValueError("Peso total deve ser maior que zero.")
        if not recipe.ingredients:
            raise ValueError("Adicione pelo menos um ingrediente.")
        for ingredient in recipe.ingredients:
            self.validate_ingredient(ingredient)

    def validate_ingredient(self, ingredient: RecipeIngredient) -> None:
        if not ingredient.name.strip():
            raise ValueError("Ingrediente deve ser informado.")
        if ingredient.quantity <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")
        if not ingredient.unit.strip():
            raise ValueError("Unidade deve ser informada.")
        if ingredient.weight_g <= 0:
            raise ValueError("Peso em gramas deve ser maior que zero.")
        values = [
            ingredient.energy_kcal,
            ingredient.protein_g,
            ingredient.carbohydrate_g,
            ingredient.fat_g,
            ingredient.fiber_g,
            ingredient.sodium_mg,
        ]
        if any(value < 0 for value in values):
            raise ValueError("Valores nutricionais nao podem ser negativos.")

    def calculate_totals(self, ingredients: list[RecipeIngredient]) -> RecipeNutrients:
        for ingredient in ingredients:
            self.validate_ingredient(ingredient)
        return RecipeNutrients(
            energy_kcal=sum(item.energy_kcal for item in ingredients),
            protein_g=sum(item.protein_g for item in ingredients),
            carbohydrate_g=sum(item.carbohydrate_g for item in ingredients),
            fat_g=sum(item.fat_g for item in ingredients),
            fiber_g=sum(item.fiber_g for item in ingredients),
            sodium_mg=sum(item.sodium_mg for item in ingredients),
        )

    def calculate_per_serving(self, recipe: Recipe) -> RecipeNutrients:
        self.validate_recipe(recipe)
        return self._divide(self._totals_from_recipe(recipe), recipe.servings)

    def calculate_per_100g(self, recipe: Recipe) -> RecipeNutrients:
        self.validate_recipe(recipe)
        factor = 100 / recipe.total_weight_g
        totals = self._totals_from_recipe(recipe)
        return RecipeNutrients(
            energy_kcal=totals.energy_kcal * factor,
            protein_g=totals.protein_g * factor,
            carbohydrate_g=totals.carbohydrate_g * factor,
            fat_g=totals.fat_g * factor,
            fiber_g=totals.fiber_g * factor,
            sodium_mg=totals.sodium_mg * factor,
        )

    def _totals_from_recipe(self, recipe: Recipe) -> RecipeNutrients:
        return RecipeNutrients(
            energy_kcal=recipe.total_energy_kcal,
            protein_g=recipe.total_protein_g,
            carbohydrate_g=recipe.total_carbohydrate_g,
            fat_g=recipe.total_fat_g,
            fiber_g=recipe.total_fiber_g,
            sodium_mg=recipe.total_sodium_mg,
        )

    def _divide(self, nutrients: RecipeNutrients, divisor: float) -> RecipeNutrients:
        return RecipeNutrients(
            energy_kcal=nutrients.energy_kcal / divisor,
            protein_g=nutrients.protein_g / divisor,
            carbohydrate_g=nutrients.carbohydrate_g / divisor,
            fat_g=nutrients.fat_g / divisor,
            fiber_g=nutrients.fiber_g / divisor,
            sodium_mg=nutrients.sodium_mg / divisor,
        )
