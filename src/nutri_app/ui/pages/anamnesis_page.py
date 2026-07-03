from __future__ import annotations

from PySide6.QtWidgets import QLabel

from nutri_app.ui.pages.base import Page


class AnamnesisPage(Page):
    def __init__(self) -> None:
        super().__init__("Anamnese", "Queixa principal, historico, rotina alimentar e sintomas.")
        self.layout.addWidget(QLabel("Roteiro: QP/HDA/HPP, historico familiar e padrao alimentar."))
        self.layout.addStretch()
