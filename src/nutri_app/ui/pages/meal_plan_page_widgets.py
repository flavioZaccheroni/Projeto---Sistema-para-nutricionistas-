from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QHeaderView, QTableWidget, QVBoxLayout


def configure_table(table: QTableWidget) -> None:
    table.setWordWrap(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)


def build_form_card(title: str, form: QFormLayout) -> QGroupBox:
    card = QGroupBox(title)
    layout = QVBoxLayout(card)
    layout.addLayout(form)
    return card
