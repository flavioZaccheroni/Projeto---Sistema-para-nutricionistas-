from __future__ import annotations

from enum import StrEnum


class BmiClassification(StrEnum):
    THINNESS = "baixo peso"
    NORMAL = "eutrofia"
    OVERWEIGHT = "sobrepeso"
    OBESITY_I = "obesidade grau I"
    OBESITY_II = "obesidade grau II"
    OBESITY_III = "obesidade grau III"


class AnthropometryService:
    REFERENCE = "Organizacao Mundial da Saude (OMS)"

    def calculate_bmi(self, weight_kg: float, height_meters: float) -> float:
        if weight_kg <= 0 or height_meters <= 0:
            raise ValueError("Peso e altura devem ser maiores que zero.")
        return weight_kg / (height_meters**2)

    def classify_adult_bmi(self, bmi: float) -> BmiClassification:
        if bmi < 18.5:
            return BmiClassification.THINNESS
        if bmi < 25:
            return BmiClassification.NORMAL
        if bmi < 30:
            return BmiClassification.OVERWEIGHT
        if bmi < 35:
            return BmiClassification.OBESITY_I
        if bmi < 40:
            return BmiClassification.OBESITY_II
        return BmiClassification.OBESITY_III

    def calculate_weight_loss_percentage(
        self,
        usual_weight_kg: float,
        current_weight_kg: float,
    ) -> float:
        if usual_weight_kg <= 0 or current_weight_kg <= 0:
            raise ValueError("Pesos devem ser maiores que zero.")
        return ((usual_weight_kg - current_weight_kg) / usual_weight_kg) * 100

    def has_high_nutritional_risk_by_weight_loss(self, percentage: float) -> bool:
        return percentage > 10

    def calculate_waist_hip_ratio(self, waist_cm: float, hip_cm: float) -> float:
        if waist_cm <= 0 or hip_cm <= 0:
            raise ValueError("Cintura e quadril devem ser maiores que zero.")
        return waist_cm / hip_cm

    def calculate_waist_height_ratio(self, waist_cm: float, height_meters: float) -> float:
        if waist_cm <= 0 or height_meters <= 0:
            raise ValueError("Cintura e altura devem ser maiores que zero.")
        return waist_cm / (height_meters * 100)

    def classify_waist_hip_ratio(self, ratio: float, biological_sex: str) -> str:
        cutoff = 0.90 if biological_sex == "Masculino" else 0.85
        if ratio <= cutoff:
            return "sem risco aumentado"
        return "risco cardiovascular aumentado"

    def classify_waist_circumference(self, waist_cm: float, biological_sex: str) -> str:
        if biological_sex == "Masculino":
            if waist_cm < 94:
                return "sem risco aumentado"
            if waist_cm < 102:
                return "risco aumentado para doencas cardiovasculares e metabolicas"
            return "risco muito aumentado para doencas cardiovasculares e metabolicas"

        if waist_cm < 80:
            return "sem risco aumentado"
        if waist_cm < 88:
            return "risco aumentado para doencas cardiovasculares e metabolicas"
        return "risco muito aumentado para doencas cardiovasculares e metabolicas"

    def build_diagnosis_summary(
        self,
        biological_sex: str,
        bmi: float,
        bmi_classification: str,
        waist_cm: float | None,
        waist_hip_ratio: float | None,
    ) -> str:
        parts = [
            f"Paciente do sexo {biological_sex.lower()}.",
            (
                f"IMC de {bmi:.1f} kg/m2, classificado como "
                f"{bmi_classification} segundo a {self.REFERENCE}."
            ),
        ]
        if waist_hip_ratio is not None:
            rcq_classification = self.classify_waist_hip_ratio(waist_hip_ratio, biological_sex)
            parts.append(f"RCQ de {waist_hip_ratio:.2f}, compativel com {rcq_classification}.")
        if waist_cm is not None:
            waist_classification = self.classify_waist_circumference(waist_cm, biological_sex)
            parts.append(
                f"Circunferencia da cintura de {waist_cm:g} cm, compativel com "
                f"{waist_classification}."
            )
        parts.append(f"Referencia utilizada: {self.REFERENCE}.")
        return " ".join(parts)
