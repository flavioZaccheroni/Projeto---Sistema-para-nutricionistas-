from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nutri_app.repositories.dashboard_repository import DashboardRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.base import Page


class DashboardPage(Page):
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        super().__init__("Dashboard", "Visao inicial de pacientes, alertas e pendencias clinicas.")
        self.repository = DashboardRepository(connection_factory)

        refresh = QPushButton("Atualizar")
        refresh.setObjectName("primaryButton")
        refresh.clicked.connect(self.refresh)
        self.layout.addWidget(refresh)

        self.indicators: dict[str, QLabel] = {}

        grid = QGridLayout()
        for index, label in enumerate(
            [
                "Pacientes ativos",
                "Consultas hoje",
                "Alertas criticos",
                "Pendencias",
            ]
        ):
            card, value = self._indicator(label)
            self.indicators[label] = value
            grid.addWidget(card, index // 2, index % 2)

        self.layout.addLayout(grid)

        self.alerts_table = QTableWidget(0, 4)
        self.alerts_table.setHorizontalHeaderLabels(["Paciente", "Origem", "Mensagem", "Gravidade"])
        self.layout.addWidget(self._table_card("Alertas clinicos recentes", self.alerts_table))

        self.appointments_table = QTableWidget(0, 4)
        self.appointments_table.setHorizontalHeaderLabels(["Paciente", "Data/hora", "Tipo", "Status"])
        self.layout.addWidget(self._table_card("Proximas consultas e pendencias", self.appointments_table))

        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        summary = self.repository.summary()
        self.indicators["Pacientes ativos"].setText(str(summary.active_patients))
        self.indicators["Consultas hoje"].setText(str(summary.today_appointments))
        self.indicators["Alertas criticos"].setText(str(summary.critical_alerts))
        self.indicators["Pendencias"].setText(str(summary.pending_items))

        alerts = self.repository.recent_alerts()
        self.alerts_table.setRowCount(len(alerts))
        for row, alert in enumerate(alerts):
            self.alerts_table.setItem(row, 0, QTableWidgetItem(alert.patient_name))
            self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.source))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(alert.message))
            self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.severity))

        appointments = self.repository.upcoming_appointments()
        self.appointments_table.setRowCount(len(appointments))
        for row, appointment in enumerate(appointments):
            self.appointments_table.setItem(row, 0, QTableWidgetItem(appointment.patient_name))
            self.appointments_table.setItem(row, 1, QTableWidgetItem(appointment.scheduled_at))
            self.appointments_table.setItem(row, 2, QTableWidgetItem(appointment.kind))
            self.appointments_table.setItem(row, 3, QTableWidgetItem(appointment.status))

    def _indicator(self, label: str) -> tuple[QWidget, QLabel]:
        card = QWidget()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.addWidget(QLabel(label), 0, 0)
        number = QLabel("0")
        number.setObjectName("indicatorValue")
        layout.addWidget(number, 1, 0)
        return card, number

    def _table_card(self, title: str, table: QTableWidget) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.addWidget(QLabel(title))
        layout.addWidget(table)
        return card
