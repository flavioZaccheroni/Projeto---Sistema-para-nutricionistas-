from __future__ import annotations

from datetime import date, datetime

DATE_FORMAT = "%d-%m-%Y"
DATETIME_FORMAT = "%d-%m-%Y %H:%M"
DATE_PLACEHOLDER = "dd-mm-aaaa"
DATETIME_PLACEHOLDER = "dd-mm-aaaa HH:MM"


def format_date(value: date | None) -> str:
    return value.strftime(DATE_FORMAT) if value else ""


def format_datetime(value: datetime | None) -> str:
    return value.strftime(DATETIME_FORMAT) if value else ""


def parse_date(value: str) -> date:
    text = value.strip()
    for date_format in [DATE_FORMAT, "%m-%d-%Y"]:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return date.fromisoformat(text)


def parse_optional_date(value: str) -> date | None:
    text = value.strip()
    if not any(char.isdigit() for char in text):
        return None
    return parse_date(text) if text else None


def parse_datetime(value: str) -> datetime:
    text = value.strip()
    for date_format in [DATETIME_FORMAT, "%m-%d-%Y %H:%M"]:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return datetime.fromisoformat(text)


def today_text() -> str:
    return format_date(date.today())
