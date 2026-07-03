from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "agendada"
    CONFIRMED = "confirmada"
    COMPLETED = "realizada"
    CANCELED = "cancelada"
    PENDING = "pendente"


class AppointmentKind(StrEnum):
    FIRST_VISIT = "Consulta inicial"
    FOLLOW_UP = "Retorno"
    REMOTE = "Teleconsulta"
    PROCEDURE = "Procedimento"


@dataclass(frozen=True)
class Appointment:
    patient_id: int
    scheduled_at: datetime
    kind: AppointmentKind
    status: AppointmentStatus
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
