from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class WebPortalCard:
    title: str
    value: str
    detail: str = ""


@dataclass(frozen=True)
class WebPortalItem:
    title: str
    description: str
    meta: str = ""


@dataclass(frozen=True)
class WebPortalSnapshot:
    cards: list[WebPortalCard] = field(default_factory=list)
    publications: list[WebPortalItem] = field(default_factory=list)
    appointments: list[WebPortalItem] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass(frozen=True)
class WebPortalPublishRecord:
    title: str
    output_path: str
    status: str
    total_pages: int
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
