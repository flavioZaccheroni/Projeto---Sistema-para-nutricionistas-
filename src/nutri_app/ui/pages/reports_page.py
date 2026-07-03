from __future__ import annotations

from PySide6.QtWidgets import QLabel

from nutri_app.ui.pages.base import Page


class ReportsPage(Page):
    def __init__(self) -> None:
        super().__init__("Relatorios", "Base para relatorio clinico, evolucao e plano alimentar.")
        self.layout.addWidget(QLabel("A geracao em PDF/Word sera implementada na fase de relatorios."))
        self.layout.addStretch()
