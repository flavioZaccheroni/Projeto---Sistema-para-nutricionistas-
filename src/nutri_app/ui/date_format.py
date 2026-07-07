from __future__ import annotations

from datetime import date, datetime

DATE_FORMAT = "%m-%d-%Y"
DATETIME_FORMAT = "%m-%d-%Y %H:%M"
DATE_PLACEHOLDER = "mm-dd-aaaa"
DATETIME_PLACEHOLDER = "mm-dd-aaaa HH:MM"


def format_date(value: date | None) -> str:
    return value.strftime(DATE_FORMAT) if value else ""


def format_datetime(value: datetime | None) -> str:
    return value.strftime(DATETIME_FORMAT) if value else ""


def parse_date(value: str) -> date:
    text = value.strip()
    try:
        return datetime.strptime(text, DATE_FORMAT).date()
    except ValueError:
        return date.fromisoformat(text)


def parse_optional_date(value: str) -> date | None:
    text = value.strip()
    return parse_date(text) if text else None


def parse_datetime(value: str) -> datetime:
    text = value.strip()
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return datetime.fromisoformat(text)


def today_text() -> str:
    return format_date(date.today())
