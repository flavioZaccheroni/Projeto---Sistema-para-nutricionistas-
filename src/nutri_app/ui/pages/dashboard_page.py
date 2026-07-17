from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nutri_app.repositories.dashboard_repository import DashboardRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.date_format import format_date, parse_datetime
from nutri_app.ui.pages.base import Page


class DashboardPage(Page):
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        super().__init__("Dashboard", "Visao inicial de pacientes, alertas e pendencias clinicas.")
        self.repository = DashboardRepository(connection_factory)

        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)
        refresh_row = QHBoxLayout()
        refresh_row.addStretch()
        refresh_row.addWidget(refresh)
        self.layout.addLayout(refresh_row)

        self.indicators: dict[str, QLabel] = {}

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        indicators = [
            (
                "Pacientes Ativos",
                "Pacientes ativos cadastrados com alertas e pendencias clinicas.",
            ),
            ("Consultas Hoje", ""),
            ("Alertas Criticos", "Ver Detalhes"),
            ("Pendencias Clinicas", ""),
        ]
        for index, (label, description) in enumerate(indicators):
            card, value = self._indicator(label, description)
            self.indicators[label] = value
            grid.addWidget(card, 0, index)

        self.layout.addLayout(grid)

        self.alerts_table = QTableWidget(0, 4)
        self.alerts_table.setHorizontalHeaderLabels(["Paciente", "Origem", "Mensagem", "Gravidade"])
        self._configure_alerts_table()
        self.layout.addWidget(self._table_card("Alertas clinicos recentes", self.alerts_table))

        self.appointments_table = QTableWidget(0, 6)
        self.appointments_table.setHorizontalHeaderLabels(
            ["Paciente", "ID", "Data", "Hora", "Tipo", "Status"]
        )
        self._configure_appointments_table()
        self.layout.addWidget(
            self._table_card("Proximas consultas e pendencias", self.appointments_table)
        )

        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        summary = self.repository.summary()
        self.indicators["Pacientes Ativos"].setText(str(summary.active_patients))
        self.indicators["Consultas Hoje"].setText(str(summary.today_appointments))
        self.indicators["Alertas Criticos"].setText(str(summary.critical_alerts))
        self.indicators["Pendencias Clinicas"].setText(str(summary.pending_items))

        alerts = self.repository.recent_alerts()
        self.alerts_table.setRowCount(len(alerts))
        for row, alert in enumerate(alerts):
            self.alerts_table.setItem(row, 0, QTableWidgetItem(alert.patient_name))
            self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.source))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(alert.message))
            self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.severity))
        self.alerts_table.resizeRowsToContents()

        appointments = self.repository.upcoming_appointments()
        self.appointments_table.setRowCount(len(appointments))
        for row, appointment in enumerate(appointments):
            date_text, time_text = self._split_schedule(appointment.scheduled_at)
            self.appointments_table.setItem(row, 0, QTableWidgetItem(appointment.patient_name))
            self.appointments_table.setItem(row, 1, QTableWidgetItem(str(appointment.id)))
            self.appointments_table.setItem(row, 2, QTableWidgetItem(date_text))
            self.appointments_table.setItem(row, 3, QTableWidgetItem(time_text))
            self.appointments_table.setItem(row, 4, QTableWidgetItem(appointment.kind))
            self.appointments_table.setItem(row, 5, QTableWidgetItem(appointment.status))
        self.appointments_table.resizeRowsToContents()

    def _indicator(self, label: str, description: str) -> tuple[QWidget, QLabel]:
        card = QWidget()
        card.setObjectName("card")
        layout = QGridLayout(card)
        title = QLabel(label)
        title.setObjectName("dashboardCardTitle")
        layout.addWidget(title, 0, 0)
        number = QLabel("0")
        number.setObjectName("indicatorValue")
        layout.addWidget(number, 1, 0)
        icon = QLabel(self._indicator_icon(label))
        icon.setObjectName("dashboardIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(icon, 0, 1, 2, 1)
        if description:
            description_label = QLabel(description)
            description_label.setObjectName("mutedText")
            description_label.setWordWrap(True)
            layout.addWidget(description_label, 2, 0, 1, 2)
        if label == "Alertas Criticos":
            card.setObjectName("dangerCard")
        return card, number

    def _table_card(self, title: str, table: QTableWidget) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        header = QHBoxLayout()
        label = QLabel(title)
        label.setObjectName("dashboardSectionTitle")
        header.addWidget(label)
        header.addStretch()
        header.addWidget(QLabel("^"))
        layout.addLayout(header)
        layout.addWidget(table)
        return card

    def _indicator_icon(self, label: str) -> str:
        icons = {
            "Pacientes Ativos": "P+",
            "Consultas Hoje": "OK",
            "Alertas Criticos": "!",
            "Pendencias Clinicas": "->",
        }
        return icons.get(label, "")

    def _configure_alerts_table(self) -> None:
        self.alerts_table.setWordWrap(True)
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.alerts_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def _configure_appointments_table(self) -> None:
        self.appointments_table.setWordWrap(True)
        header = self.appointments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.appointments_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def _split_schedule(self, scheduled_at: str) -> tuple[str, str]:
        try:
            parsed = parse_datetime(scheduled_at)
        except ValueError:
            date_text, _, time_text = scheduled_at.partition(" ")
            return date_text, time_text
        return format_date(parsed.date()), parsed.strftime("%H:%M")
