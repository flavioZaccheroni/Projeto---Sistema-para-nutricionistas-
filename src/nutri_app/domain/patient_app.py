from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class PatientPublicationType(StrEnum):
    MEAL_PLAN = "Plano alimentar"
    GUIDANCE = "Orientacao"
    MESSAGE = "Mensagem"


class PatientPublicationStatus(StrEnum):
    DRAFT = "Rascunho"
    PUBLISHED = "Publicado"
    ARCHIVED = "Arquivado"


@dataclass(frozen=True)
class PatientAppAccess:
    patient_id: int
    email_login: str
    access_code: str
    active: bool = True
    last_access: datetime | None = None
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PatientAppPublication:
    patient_id: int
    publication_type: PatientPublicationType
    title: str
    content: str
    status: PatientPublicationStatus = PatientPublicationStatus.PUBLISHED
    publication_date: date = field(default_factory=date.today)
    meal_plan_id: int | None = None
    expiration_date: date | None = None
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    meal_plan_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PatientAppAdherence:
    patient_id: int
    record_date: date
    adherence_percent: float
    publication_id: int | None = None
    mood: str = ""
    difficulties: str = ""
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    publication_title: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PatientAppSummary:
    total_accesses: int = 0
    total_published: int = 0
    average_adherence: float = 0
