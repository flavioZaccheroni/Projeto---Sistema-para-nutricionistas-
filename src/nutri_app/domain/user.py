from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    ADMINISTRADOR = "Administrador"
    NUTRICIONISTA = "Nutricionista"
    RECEPCIONISTA = "Recepcionista"
    AUDITOR = "Auditor"


@dataclass(frozen=True)
class User:
    name: str
    email: str
    password_hash: str
    role: UserRole
    active: bool = True
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    name: str
    email: str
    role: UserRole


@dataclass(frozen=True)
class Permission:
    role: UserRole
    module: str
    can_view: bool
    can_create: bool
    can_edit: bool
    can_delete: bool
    can_export: bool
