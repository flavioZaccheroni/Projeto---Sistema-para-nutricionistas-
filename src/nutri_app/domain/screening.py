from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ScreeningProtocol(StrEnum):
    NRS_2002 = "NRS-2002"
    MUST = "MUST"
    MST = "MST"
    SGA = "SGA/ASG"
    MNA = "MNA"
    MNA_SF = "MNA-SF"
    STRONGKIDS = "STRONGkids"
    MIS = "MIS"


@dataclass(frozen=True)
class Screening:
    patient_id: int
    protocol: ScreeningProtocol
    score: float
    classification: str
    appointment_id: int | None = None
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
