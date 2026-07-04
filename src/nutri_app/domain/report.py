from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ClinicalReport:
    report_type: str
    title: str
    patient_id: int | None = None
    patient_name: str = ""
    file_path: str = ""
    parameters: str = ""
    content: str = ""
    status: str = "Gerado"
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
