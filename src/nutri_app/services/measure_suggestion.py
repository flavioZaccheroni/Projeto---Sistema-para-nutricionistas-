from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from nutri_app.domain.anthropometry import Anthropometry
from nutri_app.domain.patient import calculate_age

ADULT_AGE = 18
MAX_MEASURE_AGE_DAYS = 90


@dataclass(frozen=True)
class MeasureSuggestion:
    """Valores sugeridos para preencher um formulario, ja na unidade da tela."""

    age_years: int
    age_months: int
    weight_kg: float | None = None
    height_cm: float | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    source_date: date | None = None


def age_in_months(birth_date: date, on: date) -> int:
    months = (on.year - birth_date.year) * 12 + (on.month - birth_date.month)
    if on.day < birth_date.day:
        months -= 1
    return max(months, 0)


def suggest_measures(
    birth_date: date,
    latest: Anthropometry | None,
    today: date | None = None,
) -> MeasureSuggestion:
    """Idade sempre; peso/medidas so se a ultima antropometria for recente.

    Peso e circunferencias mudam rapido, entao so valem por MAX_MEASURE_AGE_DAYS.
    A altura de um adulto muda pouco e vale sem limite; em menores segue a mesma
    janela do peso, pois a crianca cresce.
    """
    reference = today or date.today()
    suggestion = MeasureSuggestion(
        age_years=calculate_age(birth_date, reference),
        age_months=age_in_months(birth_date, reference),
    )
    if latest is None:
        return suggestion

    age_days = (reference - latest.assessment_date).days
    recent = 0 <= age_days <= MAX_MEASURE_AGE_DAYS
    is_adult = calculate_age(birth_date, reference) >= ADULT_AGE

    weight = latest.weight_kg if recent else None
    waist = latest.waist_cm if recent else None
    hip = latest.hip_cm if recent else None
    height = latest.height_m * 100 if (recent or (is_adult and age_days >= 0)) else None

    return MeasureSuggestion(
        age_years=suggestion.age_years,
        age_months=suggestion.age_months,
        weight_kg=weight,
        height_cm=height,
        waist_cm=waist,
        hip_cm=hip,
        source_date=latest.assessment_date if any([weight, height, waist, hip]) else None,
    )
