from __future__ import annotations

from PySide6.QtWidgets import QLabel

from nutri_app.ui.pages.base import Page


class ModulePlaceholderPage(Page):
    def __init__(self, title: str, subtitle: str, phase: str, scope_items: list[str]) -> None:
        super().__init__(title, subtitle)

        phase_label = QLabel(f"Planejado para {phase}.")
        phase_label.setObjectName("pageSubtitle")
        self.layout.addWidget(phase_label)

        for item in scope_items:
            label = QLabel(f"- {item}")
            label.setWordWrap(True)
            self.layout.addWidget(label)

        self.layout.addStretch()
