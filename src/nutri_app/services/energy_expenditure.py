from __future__ import annotations

from dataclasses import dataclass

from nutri_app.domain.energy_expenditure import BiologicalSex, EnergyEquation
from nutri_app.services.clinical_validation import ClinicalValidationMatrix


@dataclass(frozen=True)
class MacronutrientTargets:
    protein_g: float
    carbohydrate_g: float
    fat_g: float


@dataclass(frozen=True)
class CalculationTrace:
    formula: str
    reference: str
    details: str


class EnergyExpenditureService:
    EQUATION_REFERENCES = {
        EnergyEquation.MIFFLIN_ST_JEOR: "Mifflin-St. Jeor (1990)",
        EnergyEquation.HARRIS_BENEDICT: "Harris-Benedict (1919/1984)",
        EnergyEquation.FAO_WHO: "FAO/WHO/UNU",
        EnergyEquation.DRI: "IOM/DRI",
        EnergyEquation.OWEN: "Owen",
        EnergyEquation.SCHOFIELD: "Schofield",
        EnergyEquation.CUNNINGHAM: "Cunningham",
        EnergyEquation.KATCH_MCARDLE: "Katch-McArdle",
    }
    EQUATION_REFERENCE_KEYS = {
        EnergyEquation.MIFFLIN_ST_JEOR: "Mifflin-St. Jeor",
        EnergyEquation.HARRIS_BENEDICT: "Harris-Benedict",
        EnergyEquation.FAO_WHO: "FAO/WHO/UNU",
        EnergyEquation.DRI: "DRI",
        EnergyEquation.OWEN: "Owen",
        EnergyEquation.SCHOFIELD: "Schofield",
        EnergyEquation.CUNNINGHAM: "Cunningham",
        EnergyEquation.KATCH_MCARDLE: "Katch-McArdle",
    }
    ACTIVITY_FACTORS = {
        "Sedentario": 1.20,
        "Pouco ativo": 1.375,
        "Moderadamente ativo": 1.55,
        "Muito ativo": 1.725,
    }
    STRESS_FACTORS = {
        "Sem estresse metabolico": 1.00,
        "Pos-operatorio eletivo": 1.20,
        "Infeccao leve": 1.20,
        "Infeccao moderada": 1.30,
        "Infeccao grave": 1.50,
        "Trauma": 1.35,
        "Queimaduras": 1.80,
        "Sepse": 1.60,
        "Paciente critico": 1.40,
    }
    GOAL_ADJUSTMENTS = {
        "Manutencao de peso": 0.0,
        "Perda de peso leve": -0.10,
        "Perda de peso moderada": -0.20,
        "Perda de peso intensa": -0.30,
        "Ganho de peso leve": 0.10,
        "Ganho de peso moderado": 0.20,
        "Ganho de peso intenso": 0.30,
    }

    def calculate_basal_energy(
        self,
        equation: EnergyEquation,
        sex: BiologicalSex,
        age_years: int,
        weight_kg: float,
        height_cm: float,
        lean_mass_kg: float | None = None,
        activity_factor: float = 1.0,
    ) -> float:
        self._validate_common(age_years, weight_kg, height_cm)

        if equation == EnergyEquation.HARRIS_BENEDICT:
            return self._harris_benedict(sex, age_years, weight_kg, height_cm)
        if equation == EnergyEquation.MIFFLIN_ST_JEOR:
            return self._mifflin_st_jeor(sex, age_years, weight_kg, height_cm)
        if equation == EnergyEquation.OWEN:
            return self._owen(sex, weight_kg)
        if equation == EnergyEquation.SCHOFIELD:
            return self._schofield(sex, age_years, weight_kg)
        if equation == EnergyEquation.FAO_WHO:
            return self._fao_who(sex, age_years, weight_kg)
        if equation == EnergyEquation.CUNNINGHAM:
            return 500 + 22 * self._required_lean_mass(lean_mass_kg, equation)
        if equation == EnergyEquation.KATCH_MCARDLE:
            return 370 + 21.6 * self._required_lean_mass(lean_mass_kg, equation)
        if equation == EnergyEquation.DRI:
            return self._dri_eer(sex, age_years, weight_kg, height_cm, activity_factor)

        raise ValueError("Equacao de gasto energetico nao suportada.")

    def calculate_total_energy(
        self,
        basal_energy_kcal: float,
        activity_factor: float,
        stress_factor: float,
        goal_adjustment_kcal: float = 0,
        equation: EnergyEquation | None = None,
    ) -> float:
        if basal_energy_kcal <= 0:
            raise ValueError("TMB deve ser maior que zero.")
        if activity_factor <= 0:
            raise ValueError("Fator de atividade deve ser maior que zero.")
        if stress_factor <= 0:
            raise ValueError("Fator de estresse deve ser maior que zero.")

        multiplier = (
            stress_factor if equation == EnergyEquation.DRI else activity_factor * stress_factor
        )
        return basal_energy_kcal * multiplier + goal_adjustment_kcal

    def calculate_macronutrients(
        self,
        total_energy_kcal: float,
        weight_kg: float,
        protein_g_per_kg: float,
        fat_percentage: float,
    ) -> MacronutrientTargets:
        if total_energy_kcal <= 0:
            raise ValueError("GET deve ser maior que zero.")
        if weight_kg <= 0:
            raise ValueError("Peso deve ser maior que zero.")
        if protein_g_per_kg <= 0:
            raise ValueError("Proteina por kg deve ser maior que zero.")
        if fat_percentage < 0 or fat_percentage >= 100:
            raise ValueError("Percentual de lipidios deve estar entre 0 e 99.")

        protein_g = weight_kg * protein_g_per_kg
        protein_kcal = protein_g * 4
        fat_g = (total_energy_kcal * (fat_percentage / 100)) / 9
        fat_kcal = fat_g * 9
        carbohydrate_kcal = total_energy_kcal - protein_kcal - fat_kcal
        if carbohydrate_kcal < 0:
            raise ValueError("Distribuicao de macros excede o GET calculado.")
        return MacronutrientTargets(
            protein_g=protein_g,
            carbohydrate_g=carbohydrate_kcal / 4,
            fat_g=fat_g,
        )

    def calculate_goal_adjustment(self, total_energy_kcal: float, goal: str) -> float:
        return total_energy_kcal * self.GOAL_ADJUSTMENTS.get(goal, 0.0)

    def calculate_energy_by_weight(self, weight_kg: float, kcal_per_kg: float) -> float:
        if weight_kg <= 0 or kcal_per_kg <= 0:
            raise ValueError("Peso e kcal/kg devem ser maiores que zero.")
        return weight_kg * kcal_per_kg

    def reference_for(self, equation: EnergyEquation) -> str:
        key = self.EQUATION_REFERENCE_KEYS.get(equation)
        if key is None:
            return self.EQUATION_REFERENCES.get(equation, equation.value)
        return ClinicalValidationMatrix.summary_for(key)

    def build_trace(
        self,
        equation: EnergyEquation,
        basal: float,
        activity_category: str,
        activity_factor: float,
        stress_condition: str,
        stress_factor: float,
        goal: str,
        goal_adjustment: float,
        total: float,
        weight_kg: float,
        kcal_per_kg: float,
        protein_g_per_kg: float,
        protein_g: float,
    ) -> CalculationTrace:
        reference = (
            f"{self.reference_for(equation)}; IOM/DRI para atividade; "
            "BRASPEN/AMB para estresse metabolico; DRIs para distribuicao nutricional."
        )
        formula = "GET = TMB x Fator de Atividade x Fator de Injuria + Ajuste de Objetivo"
        details = (
            f"TMB/GEB: {basal:.0f} kcal/dia. "
            f"Atividade: {activity_category} ({activity_factor:g}). "
            f"Estresse/injuria: {stress_condition} ({stress_factor:g}). "
            f"Objetivo: {goal} ({goal_adjustment:+.0f} kcal). "
            f"GET final: {total:.0f} kcal/dia. "
            f"Prescricao por peso: {weight_kg:g} kg x {kcal_per_kg:g} kcal/kg = "
            f"{self.calculate_energy_by_weight(weight_kg, kcal_per_kg):.0f} kcal/dia. "
            f"Proteina: {weight_kg:g} kg x {protein_g_per_kg:g} g/kg = {protein_g:.1f} g/dia."
        )
        return CalculationTrace(formula=formula, reference=reference, details=details)

    def _validate_common(self, age_years: int, weight_kg: float, height_cm: float) -> None:
        if age_years <= 0:
            raise ValueError("Idade deve ser maior que zero.")
        if weight_kg <= 0:
            raise ValueError("Peso deve ser maior que zero.")
        if height_cm <= 0:
            raise ValueError("Altura deve ser maior que zero.")

    def _required_lean_mass(self, lean_mass_kg: float | None, equation: EnergyEquation) -> float:
        if lean_mass_kg is None or lean_mass_kg <= 0:
            raise ValueError(f"{equation.value} exige massa magra maior que zero.")
        return lean_mass_kg

    def _harris_benedict(
        self,
        sex: BiologicalSex,
        age_years: int,
        weight_kg: float,
        height_cm: float,
    ) -> float:
        if sex == BiologicalSex.MALE:
            return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age_years)
        return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age_years)

    def _mifflin_st_jeor(
        self,
        sex: BiologicalSex,
        age_years: int,
        weight_kg: float,
        height_cm: float,
    ) -> float:
        sex_constant = 5 if sex == BiologicalSex.MALE else -161
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + sex_constant

    def _owen(self, sex: BiologicalSex, weight_kg: float) -> float:
        if sex == BiologicalSex.MALE:
            return 879 + (10.2 * weight_kg)
        return 795 + (7.18 * weight_kg)

    def _schofield(self, sex: BiologicalSex, age_years: int, weight_kg: float) -> float:
        if sex == BiologicalSex.MALE:
            if age_years < 30:
                return (15.057 * weight_kg) + 692.2
            if age_years < 60:
                return (11.472 * weight_kg) + 873.1
            return (11.711 * weight_kg) + 587.7

        if age_years < 30:
            return (14.818 * weight_kg) + 486.6
        if age_years < 60:
            return (8.126 * weight_kg) + 845.6
        return (9.082 * weight_kg) + 658.5

    def _fao_who(self, sex: BiologicalSex, age_years: int, weight_kg: float) -> float:
        if sex == BiologicalSex.MALE:
            if age_years < 30:
                return (15.3 * weight_kg) + 679
            if age_years < 60:
                return (11.6 * weight_kg) + 879
            return (13.5 * weight_kg) + 487

        if age_years < 30:
            return (14.7 * weight_kg) + 496
        if age_years < 60:
            return (8.7 * weight_kg) + 829
        return (10.5 * weight_kg) + 596

    def _dri_eer(
        self,
        sex: BiologicalSex,
        age_years: int,
        weight_kg: float,
        height_cm: float,
        activity_factor: float,
    ) -> float:
        height_m = height_cm / 100
        if sex == BiologicalSex.MALE:
            return (
                662
                - (9.53 * age_years)
                + activity_factor * ((15.91 * weight_kg) + (539.6 * height_m))
            )
        return 354 - (6.91 * age_years) + activity_factor * ((9.36 * weight_kg) + (726 * height_m))
