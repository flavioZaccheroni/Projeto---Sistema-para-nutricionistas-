from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class IntegrationType(StrEnum):
    LABORATORY = "Laboratorio"
    FINANCIAL = "Financeiro"
    PATIENT_APP = "App paciente"
    WEBHOOK = "Webhook"
    OTHER = "Outro"


class IntegrationDirection(StrEnum):
    IMPORT = "Importacao"
    EXPORT = "Exportacao"


class IntegrationStatus(StrEnum):
    CONFIGURED = "Configurada"
    SUCCESS = "Sucesso"
    FAILED = "Falhou"


@dataclass(frozen=True)
class ExternalIntegration:
    name: str
    integration_type: IntegrationType
    endpoint: str = ""
    active: bool = True
    credential_alias: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class IntegrationExecution:
    direction: IntegrationDirection
    entity: str
    status: IntegrationStatus
    integration_id: int | None = None
    payload: str = ""
    result: str = ""
    id: int | None = None
    integration_name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
