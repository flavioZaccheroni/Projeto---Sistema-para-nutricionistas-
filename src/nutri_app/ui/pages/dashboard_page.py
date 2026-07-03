from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from nutri_app.ui.pages.base import Page


class DashboardPage(Page):
    def __init__(self) -> None:
        super().__init__("Dashboard", "Visao inicial de pacientes, alertas e pendencias clinicas.")

        grid = QGridLayout()
        for index, (label, value) in enumerate(
            [
                ("Pacientes ativos", "0"),
                ("Consultas hoje", "0"),
                ("Alertas criticos", "0"),
                ("Pendencias", "0"),
            ]
        ):
            grid.addWidget(self._indicator(label, value), index // 2, index % 2)

        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _indicator(self, label: str, value: str) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.addWidget(QLabel(label), 0, 0)
        number = QLabel(value)
        number.setObjectName("indicatorValue")
        layout.addWidget(number, 1, 0)
        return card
