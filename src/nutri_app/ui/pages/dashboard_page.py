from __future__ import annotations

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
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

        self.patient_filter = QComboBox()
        self.metric_filter = QComboBox()
        self.metric_filter.addItems(
            [
                "Peso (kg)",
                "IMC (kg/m2)",
                "Gordura corporal (%)",
                "Adesao (%)",
                "Alertas laboratoriais",
            ]
        )
        self.patient_filter.currentIndexChanged.connect(self._refresh_chart)
        self.metric_filter.currentIndexChanged.connect(self._refresh_chart)
        chart_filters = QHBoxLayout()
        chart_filters.addWidget(QLabel("Paciente"))
        chart_filters.addWidget(self.patient_filter, 2)
        chart_filters.addWidget(QLabel("Metrica"))
        chart_filters.addWidget(self.metric_filter, 1)
        self.chart = QChart()
        self.chart.setTitle("Evolucao clinica longitudinal")
        self.chart.legend().hide()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(260)
        chart_card = QWidget()
        chart_card.setObjectName("card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addLayout(chart_filters)
        chart_layout.addWidget(self.chart_view)
        self.layout.addWidget(chart_card)

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
        selected_patient = self.patient_filter.currentData()
        self.patient_filter.blockSignals(True)
        self.patient_filter.clear()
        for patient_id, name in self.repository.list_patients():
            self.patient_filter.addItem(name, patient_id)
        if selected_patient is not None:
            index = self.patient_filter.findData(selected_patient)
            if index >= 0:
                self.patient_filter.setCurrentIndex(index)
        self.patient_filter.blockSignals(False)
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        self.chart.removeAllSeries()
        for axis in list(self.chart.axes()):
            self.chart.removeAxis(axis)
        patient_id = self.patient_filter.currentData()
        metric = self.metric_filter.currentText()
        if patient_id is None or not metric:
            self.chart.setTitle("Evolucao clinica — selecione um paciente")
            return
        points = self.repository.evolution_series(int(patient_id), metric)
        series = QLineSeries()
        series.setName(metric)
        for date_text, value in points:
            parsed = QDateTime.fromString(date_text[:10], "yyyy-MM-dd")
            series.append(parsed.toMSecsSinceEpoch(), value)
        self.chart.addSeries(series)
        self.chart.setTitle(f"{metric} — {self.patient_filter.currentText()}")
        if not points:
            self.chart.setTitle(self.chart.title() + " (sem dados)")
            return
        from PySide6.QtCharts import QDateTimeAxis

        date_axis = QDateTimeAxis()
        date_axis.setFormat("dd/MM/yyyy")
        date_axis.setTitleText("Data")
        value_axis = QValueAxis()
        value_axis.setTitleText(metric)
        value_axis.applyNiceNumbers()
        self.chart.addAxis(date_axis, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(date_axis)
        series.attachAxis(value_axis)

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
