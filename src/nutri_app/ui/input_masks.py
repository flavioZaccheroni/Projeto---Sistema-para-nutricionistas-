from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit

from nutri_app.ui.date_format import DATE_PLACEHOLDER, DATETIME_PLACEHOLDER

EMAIL_PATTERN = r"^$|^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def apply_date_mask(field: QLineEdit, optional: bool = False) -> None:
    field.setInputMask("00-00-0000;_")
    suffix = " opcional" if optional else ""
    field.setPlaceholderText(f"{DATE_PLACEHOLDER}{suffix}")


def apply_datetime_mask(field: QLineEdit) -> None:
    field.setInputMask("00-00-0000 00:00;_")
    field.setPlaceholderText(DATETIME_PLACEHOLDER)


def apply_phone_mask(field: QLineEdit) -> None:
    field.setInputMask("(00) 00000-0000;_")
    field.setPlaceholderText("(00) 00000-0000")


def apply_email_validator(field: QLineEdit) -> None:
    field.setPlaceholderText("nome@email.com")
    field.setValidator(QRegularExpressionValidator(QRegularExpression(EMAIL_PATTERN), field))
