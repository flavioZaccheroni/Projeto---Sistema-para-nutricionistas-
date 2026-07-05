from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ReleaseCheckStatus(StrEnum):
    PASSED = "Aprovado"
    WARNING = "Atencao"
    FAILED = "Falhou"


@dataclass(frozen=True)
class ReleaseCheck:
    name: str
    status: ReleaseCheckStatus
    details: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ReleaseReadiness:
    version: str
    ready: bool
    checks: list[ReleaseCheck]

    @property
    def total_passed(self) -> int:
        return sum(1 for check in self.checks if check.status == ReleaseCheckStatus.PASSED)
