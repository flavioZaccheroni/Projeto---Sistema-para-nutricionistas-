from __future__ import annotations

from datetime import date, datetime

DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"
DATE_PLACEHOLDER = "dd/mm/aaaa"
DATETIME_PLACEHOLDER = "dd/mm/aaaa HH:MM"


def format_date(value: date | None) -> str:
    return value.strftime(DATE_FORMAT) if value else ""


def format_datetime(value: datetime | None) -> str:
    return value.strftime(DATETIME_FORMAT) if value else ""


def parse_date(value: str) -> date:
    text = value.strip()
    if not any(char.isdigit() for char in text):
        raise ValueError("Data e obrigatoria.")
    for date_format in [DATE_FORMAT, "%d-%m-%Y", "%m-%d-%Y"]:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Data invalida: {text}") from exc


def parse_optional_date(value: str) -> date | None:
    text = value.strip()
    if not any(char.isdigit() for char in text):
        return None
    return parse_date(text) if text else None


def parse_datetime(value: str) -> datetime:
    text = value.strip()
    if not any(char.isdigit() for char in text):
        raise ValueError("Data e hora sao obrigatorias.")
    for date_format in [DATETIME_FORMAT, "%d-%m-%Y %H:%M", "%m-%d-%Y %H:%M"]:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Data e hora invalidas: {text}") from exc


def today_text() -> str:
    return format_date(date.today())
