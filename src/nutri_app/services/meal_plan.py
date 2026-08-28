from __future__ import annotations

from collections import defaultdict

from nutri_app.domain.food import Food
from nutri_app.domain.meal_plan import Meal, MealPlan, MealPlanItem
from nutri_app.services.food import FoodService


class MealPlanService:
    def build_item_from_food(
        self,
        food: Food,
        quantity_g: float,
        substitutions: str = "",
        food_service: FoodService | None = None,
    ) -> MealPlanItem:
        nutrients = (food_service or FoodService()).calculate_portion(food, quantity_g)
        return MealPlanItem(
            food=food.name,
            quantity=quantity_g,
            unit="g",
            energy_kcal=nutrients.energy_kcal,
            protein_g=nutrients.protein_g,
            carbohydrate_g=nutrients.carbohydrate_g,
            fat_g=nutrients.fat_g,
            substitutions=substitutions,
            food_id=food.id,
        )

    def calculate_totals(self, meals: list[Meal]) -> tuple[float, float, float, float]:
        energy = protein = carbohydrate = fat = 0.0
        for meal in meals:
            for item in meal.items:
                self.validate_item(item)
                energy += item.energy_kcal
                protein += item.protein_g
                carbohydrate += item.carbohydrate_g
                fat += item.fat_g
        return energy, protein, carbohydrate, fat

    def build_shopping_list(self, meals: list[Meal]) -> str:
        grouped: dict[tuple[str, str], float] = defaultdict(float)
        for meal in meals:
            for item in meal.items:
                grouped[(item.food.strip().lower(), item.unit.strip())] += item.quantity
        lines = []
        for (food, unit), quantity in sorted(grouped.items()):
            lines.append(f"{food}: {quantity:g} {unit}")
        return "\n".join(lines)

    def validate_plan(self, plan: MealPlan) -> None:
        if not plan.objective.strip():
            raise ValueError("Objetivo do plano deve ser informado.")
        if not plan.meals:
            raise ValueError("Adicione pelo menos uma refeicao ao plano.")
        for meal in plan.meals:
            self.validate_meal(meal)

    def validate_meal(self, meal: Meal) -> None:
        if not meal.name.strip():
            raise ValueError("Nome da refeicao deve ser informado.")
        if not meal.items:
            raise ValueError("Adicione pelo menos um item na refeicao.")

    def validate_item(self, item: MealPlanItem) -> None:
        if not item.food.strip():
            raise ValueError("Alimento deve ser informado.")
        if item.quantity <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")
        if not item.unit.strip():
            raise ValueError("Unidade deve ser informada.")
        for value in [item.energy_kcal, item.protein_g, item.carbohydrate_g, item.fat_g]:
            if value < 0:
                raise ValueError("Valores nutricionais nao podem ser negativos.")
