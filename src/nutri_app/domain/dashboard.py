from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardSummary:
    active_patients: int
    today_appointments: int
    critical_alerts: int
    pending_items: int


@dataclass(frozen=True)
class DashboardAlert:
    patient_name: str
    source: str
    message: str
    severity: str


@dataclass(frozen=True)
class DashboardAppointment:
    patient_name: str
    scheduled_at: str
    kind: str
    status: str
