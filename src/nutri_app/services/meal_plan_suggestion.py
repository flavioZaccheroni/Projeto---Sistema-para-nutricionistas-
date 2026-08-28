from __future__ import annotations

from dataclasses import dataclass

from nutri_app.domain.food import Food, FoodGroup
from nutri_app.domain.meal_plan import Meal, MealPlanItem
from nutri_app.services.food import FoodService
from nutri_app.services.meal_plan import MealPlanService

MAX_ITEM_QUANTITY_G = 400.0
MIN_ITEM_QUANTITY_G = 10.0
MIN_USABLE_ENERGY_KCAL = 1.0


@dataclass(frozen=True)
class MealTemplate:
    name: str
    time: str
    energy_percentage: float
    groups: tuple[FoodGroup, ...]


BASE_MEAL_TEMPLATES: tuple[MealTemplate, ...] = (
    MealTemplate(
        "Cafe da manha",
        "07:00",
        20,
        (FoodGroup.CEREAIS_TUBERCULOS, FoodGroup.FRUTAS, FoodGroup.LATICINIOS),
    ),
    MealTemplate("Lanche da manha", "10:00", 10, (FoodGroup.FRUTAS, FoodGroup.ACUCARES_DOCES)),
    MealTemplate(
        "Almoco",
        "12:30",
        30,
        (
            FoodGroup.CEREAIS_TUBERCULOS,
            FoodGroup.LEGUMINOSAS,
            FoodGroup.CARNES_OVOS,
            FoodGroup.HORTALICAS,
            FoodGroup.GORDURAS_OLEOS,
        ),
    ),
    MealTemplate("Lanche da tarde", "15:30", 10, (FoodGroup.LATICINIOS, FoodGroup.ACUCARES_DOCES)),
    MealTemplate(
        "Jantar",
        "19:00",
        20,
        (FoodGroup.CEREAIS_TUBERCULOS, FoodGroup.CARNES_OVOS, FoodGroup.HORTALICAS),
    ),
    MealTemplate("Ceia", "21:30", 10, (FoodGroup.LATICINIOS, FoodGroup.FRUTAS)),
)

GENERIC_MEAL_GROUPS: tuple[FoodGroup, ...] = (
    FoodGroup.CEREAIS_TUBERCULOS,
    FoodGroup.CARNES_OVOS,
    FoodGroup.HORTALICAS,
    FoodGroup.FRUTAS,
)

DEFAULT_GROUP_SHARE: dict[FoodGroup, float] = {
    FoodGroup.CEREAIS_TUBERCULOS: 35,
    FoodGroup.LEGUMINOSAS: 15,
    FoodGroup.CARNES_OVOS: 30,
    FoodGroup.HORTALICAS: 10,
    FoodGroup.FRUTAS: 15,
    FoodGroup.LATICINIOS: 20,
    FoodGroup.GORDURAS_OLEOS: 10,
    FoodGroup.ACUCARES_DOCES: 5,
}


@dataclass(frozen=True)
class ProfileRule:
    excluded_groups: frozenset[FoodGroup] = frozenset()
    max_sodium_mg: float | None = None
    preferred_keywords: tuple[str, ...] = ()
    boosted_groups: frozenset[FoodGroup] = frozenset()
    reduced_groups: frozenset[FoodGroup] = frozenset()
    prefer_low_glycemic_index: bool = False
    caution_note: str = ""


PROFILE_RULES: dict[str, ProfileRule] = {
    "Diabetes": ProfileRule(
        excluded_groups=frozenset({FoodGroup.ACUCARES_DOCES}),
        prefer_low_glycemic_index=True,
    ),
    "DASH": ProfileRule(
        max_sodium_mg=140,
        boosted_groups=frozenset({FoodGroup.HORTALICAS, FoodGroup.FRUTAS}),
    ),
    "Mediterranea": ProfileRule(
        preferred_keywords=("peixe", "salmao", "atum", "tilapia", "azeite", "azeitona"),
        boosted_groups=frozenset(
            {FoodGroup.GORDURAS_OLEOS, FoodGroup.HORTALICAS, FoodGroup.FRUTAS}
        ),
    ),
    "Hemodialise": ProfileRule(
        reduced_groups=frozenset({FoodGroup.HORTALICAS, FoodGroup.FRUTAS}),
        caution_note=(
            "Ajuste fino de potassio, fosforo e liquidos exige revisao manual da "
            "nutricionista; o Banco de Alimentos ainda nao cadastra esses micronutrientes."
        ),
    ),
    "Hipertrofia": ProfileRule(boosted_groups=frozenset({FoodGroup.CARNES_OVOS})),
    "Emagrecimento": ProfileRule(),
}


@dataclass(frozen=True)
class SuggestedMealPlan:
    meals: list[Meal]
    substitution_notes: list[str]
    caution_note: str


class MealPlanSuggestionService:
    def suggest(
        self,
        profile: str,
        target_energy_kcal: float,
        meal_count: int,
        excluded_terms: list[str],
        foods: list[Food],
        food_service: FoodService | None = None,
    ) -> SuggestedMealPlan:
        if target_energy_kcal <= 0:
            raise ValueError("Meta de energia deve ser maior que zero.")
        if meal_count <= 0:
            raise ValueError("Numero de refeicoes deve ser maior que zero.")

        service = food_service or FoodService()
        meal_plan_service = MealPlanService()
        rule = PROFILE_RULES.get(profile, ProfileRule())
        templates = self._templates_for(meal_count)
        normalized_excluded = [term.strip().lower() for term in excluded_terms if term.strip()]

        meals: list[Meal] = []
        substitution_notes: list[str] = []
        for template in templates:
            meal_energy = target_energy_kcal * (template.energy_percentage / 100)
            items, notes = self._build_meal_items(
                template, meal_energy, rule, normalized_excluded, foods, service, meal_plan_service
            )
            meals.append(Meal(name=template.name, time=template.time, items=items))
            substitution_notes.extend(notes)

        if not any(meal.items for meal in meals):
            raise ValueError(
                "Nao ha alimentos cadastrados suficientes no Banco de Alimentos para "
                "gerar a sugestao. Cadastre mais alimentos por grupo alimentar."
            )

        return SuggestedMealPlan(
            meals=meals,
            substitution_notes=substitution_notes,
            caution_note=rule.caution_note,
        )

    def _templates_for(self, meal_count: int) -> tuple[MealTemplate, ...]:
        if meal_count == len(BASE_MEAL_TEMPLATES):
            return BASE_MEAL_TEMPLATES
        share = 100 / meal_count
        return tuple(
            MealTemplate(f"Refeicao {index + 1}", "", share, GENERIC_MEAL_GROUPS)
            for index in range(meal_count)
        )

    def _build_meal_items(
        self,
        template: MealTemplate,
        meal_energy_kcal: float,
        rule: ProfileRule,
        excluded_terms: list[str],
        foods: list[Food],
        food_service: FoodService,
        meal_plan_service: MealPlanService,
    ) -> tuple[list[MealPlanItem], list[str]]:
        active_groups = [group for group in template.groups if group not in rule.excluded_groups]
        shares = self._group_shares(active_groups, rule)

        items: list[MealPlanItem] = []
        notes: list[str] = []
        for group, share_percentage in shares.items():
            candidates = self._candidates_for_group(group, foods, rule, excluded_terms)
            if not candidates:
                continue
            chosen = candidates[0]
            group_energy = meal_energy_kcal * (share_percentage / 100)
            quantity_g = self._quantity_for_energy(chosen, group_energy)
            items.append(
                meal_plan_service.build_item_from_food(
                    chosen, quantity_g, food_service=food_service
                )
            )
            alternatives = [food.name for food in candidates[1:5]]
            if alternatives:
                notes.append(
                    f"Substituicoes em {group.value}: {', '.join(alternatives)} "
                    "(equivalencia aproximada por energia)."
                )
        return items, notes

    def _group_shares(
        self, groups: list[FoodGroup], rule: ProfileRule
    ) -> dict[FoodGroup, float]:
        weights = {}
        for group in groups:
            weight = DEFAULT_GROUP_SHARE.get(group, 10)
            if group in rule.boosted_groups:
                weight *= 1.5
            if group in rule.reduced_groups:
                weight *= 0.5
            weights[group] = weight
        total = sum(weights.values())
        if total <= 0:
            return {}
        return {group: (weight / total) * 100 for group, weight in weights.items()}

    def _candidates_for_group(
        self,
        group: FoodGroup,
        foods: list[Food],
        rule: ProfileRule,
        excluded_terms: list[str],
    ) -> list[Food]:
        candidates = [
            food
            for food in foods
            if food.category == group.value
            and food.energy_kcal > MIN_USABLE_ENERGY_KCAL
            and not self._is_excluded(food, excluded_terms)
        ]
        if rule.max_sodium_mg is not None:
            candidates = [food for food in candidates if food.sodium_mg <= rule.max_sodium_mg]

        def sort_key(food: Food) -> tuple:
            keyword_rank = 0
            if rule.preferred_keywords:
                name = food.name.lower()
                matches = any(keyword in name for keyword in rule.preferred_keywords)
                keyword_rank = 0 if matches else 1
            glycemic_rank = 0.0
            if rule.prefer_low_glycemic_index:
                glycemic_rank = (
                    food.glycemic_index if food.glycemic_index is not None else 1000.0
                )
            return (keyword_rank, glycemic_rank, food.name)

        return sorted(candidates, key=sort_key)

    def _is_excluded(self, food: Food, excluded_terms: list[str]) -> bool:
        haystack = f"{food.name} {food.category} {food.allergens}".lower()
        return any(term in haystack for term in excluded_terms)

    def _quantity_for_energy(self, food: Food, target_energy_kcal: float) -> float:
        energy_per_gram = food.energy_kcal / food.base_portion_g
        if energy_per_gram <= 0:
            return MIN_ITEM_QUANTITY_G
        quantity = target_energy_kcal / energy_per_gram
        quantity = round(quantity / 5) * 5
        return min(max(quantity, MIN_ITEM_QUANTITY_G), MAX_ITEM_QUANTITY_G)
