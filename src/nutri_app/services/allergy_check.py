from __future__ import annotations

from nutri_app.domain.food import Food
from nutri_app.domain.patient_allergy import PatientAllergy


class AllergyCheckService:
    def find_conflicts(self, allergies: list[PatientAllergy], food: Food) -> list[str]:
        haystack = f"{food.name} {food.category} {food.allergens}".lower()
        conflicts = []
        for allergy in allergies:
            term = allergy.allergen.strip().lower()
            if term and term in haystack:
                conflicts.append(allergy.allergen)
        return conflicts
