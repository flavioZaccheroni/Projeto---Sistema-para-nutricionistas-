from __future__ import annotations

from collections import defaultdict

from nutri_app.domain.meal_plan import Meal, MealPlan, MealPlanItem


class MealPlanService:
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
