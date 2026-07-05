from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class BackupStatus(StrEnum):
    CREATED = "Criado"
    VERIFIED = "Verificado"
    FAILED = "Falhou"


@dataclass(frozen=True)
class BackupRecord:
    file_path: str
    size_bytes: int
    checksum_sha256: str
    status: BackupStatus = BackupStatus.CREATED
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
