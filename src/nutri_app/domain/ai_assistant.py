from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class AIAssistantRequestType(StrEnum):
    CONSULTATION_SUMMARY = "Resumo de consulta"
    FOOD_SUGGESTIONS = "Sugestoes alimentares"
    SUBSTITUTIONS = "Substituicoes"
    ASSISTED_INTERPRETATION = "Interpretacao assistida"
    SMART_ALERTS = "Alertas inteligentes"


@dataclass(frozen=True)
class AIAssistantResult:
    request_type: AIAssistantRequestType
    result: str
    alerts: list[str] = field(default_factory=list)
    status: str = "Gerado"


@dataclass(frozen=True)
class AIAssistantExecution:
    request_type: AIAssistantRequestType
    result: str
    status: str = "Gerado"
    patient_id: int | None = None
    patient_name: str = ""
    input_text: str = ""
    alerts: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
