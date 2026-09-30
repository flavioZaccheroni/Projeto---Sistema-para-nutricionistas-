from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Patient:
    name: str
    birth_date: date
    phone: str = ""
    email: str = ""
    health_insurance: str = ""
    document: str = ""
    responsible: str = ""
    clinical_notes: str = ""
    biological_sex: str = "Feminino"
    medical_record_number: str = ""
    cns: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def calculate_age(birth_date: date, on: date | None = None) -> int:
    reference = on or date.today()
    age = reference.year - birth_date.year
    if (reference.month, reference.day) < (birth_date.month, birth_date.day):
        age -= 1
    return max(age, 1)
