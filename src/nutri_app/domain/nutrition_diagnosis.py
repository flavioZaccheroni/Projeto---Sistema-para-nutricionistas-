from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class DiagnosisProtocol(StrEnum):
    GLIM = "GLIM"
    ASPEN = "ASPEN"
    ESPEN = "ESPEN"
    BRASPEN = "BRASPEN"
    SARCOPENIA = "Sarcopenia"
    CACHEXIA = "Caquexia"
    FRAILTY = "Fragilidade"


class DiagnosisSeverity(StrEnum):
    NONE = "sem criterio"
    MILD = "leve"
    MODERATE = "moderada"
    SEVERE = "grave"


@dataclass(frozen=True)
class NutritionDiagnosis:
    patient_id: int
    diagnosis_date: date
    protocol: DiagnosisProtocol
    criteria: str
    classification: str
    severity: DiagnosisSeverity
    confirmed: bool = False
    conduct: str = ""
    notes: str = ""
    appointment_id: int | None = None
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
