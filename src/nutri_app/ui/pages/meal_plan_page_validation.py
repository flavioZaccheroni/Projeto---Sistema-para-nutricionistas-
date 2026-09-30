from __future__ import annotations

from datetime import date

from nutri_app.ui.date_format import parse_optional_date


def required_float(value: str, label: str) -> float:
    parsed = optional_float(value, label)
    if parsed is None or parsed <= 0:
        raise ValueError(f"{label} deve ser maior que zero.")
    return parsed


def optional_float(value: str, label: str) -> float | None:
    if not value.strip():
        return None
    try:
        parsed = float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"{label} deve ser numerico.") from exc
    if parsed < 0:
        raise ValueError(f"{label} nao pode ser negativo.")
    return parsed


def optional_date(value: str) -> date | None:
    return parse_optional_date(value)


def format_optional(value: float | None) -> str:
    return "" if value is None else f"{value:g}"
