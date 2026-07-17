from __future__ import annotations

from datetime import date

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.date_format import format_datetime, parse_date, parse_datetime
from nutri_app.ui.pages.base import Page


class AppointmentsPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Agenda e Consultas",
            "Marcacao, retorno, status e historico de atendimento.",
        )
        self.repository = AppointmentRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.selected_appointment_id: int | None = None
        self.patient_ids_by_index: list[int] = []

        self.patient = QComboBox()
        self.scheduled_at = QLineEdit()
        self.scheduled_at.setPlaceholderText("mm-dd-aaaa HH:MM")
        self.kind = QComboBox()
        self.kind.addItems([kind.value for kind in AppointmentKind])
        self.status = QComboBox()
        self.status.addItems([status.value for status in AppointmentStatus])
        self.notes = QTextEdit()
        self.notes.setFixedHeight(72)
        self.notes.setPlaceholderText("Observacoes")

        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_appointment)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_form)
        confirm = QPushButton("Confirmar")
        confirm.clicked.connect(lambda: self._set_status(AppointmentStatus.CONFIRMED))
        done = QPushButton("Realizada")
        done.clicked.connect(lambda: self._set_status(AppointmentStatus.COMPLETED))
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(lambda: self._set_status(AppointmentStatus.CANCELED))
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_appointment)

        actions = QHBoxLayout()
        for button in [save, new, confirm, done, cancel, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.start_filter = QLineEdit()
        self.start_filter.setPlaceholderText("Inicio mm-dd-aaaa")
        self.end_filter = QLineEdit()
        self.end_filter.setPlaceholderText("Fim mm-dd-aaaa")
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos")
        self.status_filter.addItems([status.value for status in AppointmentStatus])
        filter_button = QPushButton("Filtrar")
        filter_button.clicked.connect(self.refresh)

        filters = QHBoxLayout()
        filters.addWidget(self.start_filter)
        filters.addWidget(self.end_filter)
        filters.addWidget(self.status_filter)
        filters.addWidget(filter_button)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Data/hora", "Tipo", "Status", "Observacoes"]
        )
        self.table.cellClicked.connect(self._select_appointment_from_table)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        self.layout.addWidget(self._management_card(actions))
        self.layout.addWidget(self._filters_card(filters))
        self.layout.addWidget(self._history_card())
        self.refresh()

    def _management_card(self, actions: QHBoxLayout) -> QGroupBox:
        card = QGroupBox("Gerenciamento de Consultas")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Paciente", self.patient)
        self._add_stacked_field(layout, 0, "Data/hora", self.scheduled_at, column=2)
        self._add_stacked_field(layout, 0, "Tipo", self.kind, column=4)
        self._add_stacked_field(layout, 0, "Status", self.status, column=6)
        layout.addWidget(QLabel("Observacoes"), 2, 0, 1, 8)
        layout.addWidget(self.notes, 3, 0, 1, 8)
        layout.addLayout(actions, 4, 0, 1, 8)
        for column in [1, 3, 5, 7]:
            layout.setColumnStretch(column, 1)
        return card

    def _filters_card(self, filters: QHBoxLayout) -> QGroupBox:
        card = QGroupBox("Filtros e Visualizacao")
        layout = QGridLayout(card)
        layout.addWidget(QLabel("Filtros"), 0, 0)
        layout.addLayout(filters, 0, 1)
        layout.setColumnStretch(1, 1)
        return card

    def _history_card(self) -> QGroupBox:
        card = QGroupBox("Historico de Atendimento")
        layout = QVBoxLayout(card)
        layout.addWidget(self.table)
        return card

    def _add_stacked_field(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        widget: QWidget,
        column: int = 0,
    ) -> None:
        title = QLabel(label)
        title.setObjectName("miniHeader")
        layout.addWidget(title, row, column, 1, 2)
        layout.addWidget(widget, row + 1, column, 1, 2)

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_table()

    def _save_appointment(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Agenda", "Cadastre um paciente antes de criar consulta.")
            return

        try:
            appointment = Appointment(
                id=self.selected_appointment_id,
                patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
                scheduled_at=parse_datetime(self.scheduled_at.text()),
                kind=AppointmentKind(self.kind.currentText()),
                status=AppointmentStatus(self.status.currentText()),
                notes=self.notes.toPlainText().strip(),
            )
        except ValueError:
            QMessageBox.warning(self, "Validacao", "Use data/hora no formato mm-dd-aaaa HH:MM.")
            return

        if appointment.id is None:
            appointment_id = self.repository.add(appointment)
            self._audit("criou_consulta", appointment_id, "Consulta criada.")
        else:
            self.repository.update(appointment)
            appointment_id = appointment.id
            self._audit("atualizou_consulta", appointment_id, "Consulta atualizada.")

        self._clear_form()
        self._reload_table()

    def _set_status(self, status: AppointmentStatus) -> None:
        if self.selected_appointment_id is None:
            QMessageBox.warning(self, "Agenda", "Selecione uma consulta.")
            return

        self.repository.set_status(self.selected_appointment_id, status)
        self._audit(
            "alterou_status_consulta",
            self.selected_appointment_id,
            f"Status: {status.value}",
        )
        self._clear_form()
        self._reload_table()

    def _delete_appointment(self) -> None:
        if self.selected_appointment_id is None:
            QMessageBox.warning(self, "Agenda", "Selecione uma consulta para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir consulta",
            "Deseja excluir esta consulta? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        appointment_id = self.selected_appointment_id
        self.repository.soft_delete(appointment_id)
        self._audit("excluiu_consulta", appointment_id, "Consulta removida por exclusao logica.")
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_appointment_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        self.scheduled_at.clear()
        self.kind.setCurrentIndex(0)
        self.status.setCurrentIndex(0)
        self.notes.clear()

    def _reload_patients(self) -> None:
        patients = self.patient_repository.list_active()
        current_patient_id = None
        if self.patient.currentIndex() >= 0 and self.patient_ids_by_index:
            current_patient_id = self.patient_ids_by_index[self.patient.currentIndex()]

        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in patients:
            if patient.id is None:
                continue
            self.patient.addItem(patient.name)
            self.patient_ids_by_index.append(patient.id)

        if current_patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_patient_id))

    def _reload_table(self) -> None:
        appointments = self.repository.list_by_period(
            start=self._filter_date(self.start_filter.text()),
            end=self._filter_date(self.end_filter.text()),
            status=self._filter_status(),
        )
        self.table.setRowCount(len(appointments))
        for row, appointment in enumerate(appointments):
            self.table.setItem(row, 0, QTableWidgetItem(str(appointment.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(appointment.patient_name))
            self.table.setItem(row, 2, QTableWidgetItem(format_datetime(appointment.scheduled_at)))
            self.table.setItem(row, 3, QTableWidgetItem(appointment.kind.value))
            status_item = QTableWidgetItem(appointment.status.value)
            status_item.setBackground(self._status_color(appointment.status))
            self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, QTableWidgetItem(appointment.notes))
        self.table.resizeRowsToContents()

    def _select_appointment_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        appointment = self.repository.get(int(item.text()))
        if appointment is None:
            QMessageBox.warning(self, "Agenda", "Consulta nao encontrada.")
            self._reload_table()
            return

        self.selected_appointment_id = appointment.id
        if appointment.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(appointment.patient_id))
        self.scheduled_at.setText(format_datetime(appointment.scheduled_at))
        self.kind.setCurrentText(appointment.kind.value)
        self.status.setCurrentText(appointment.status.value)
        self.notes.setPlainText(appointment.notes)

    def _filter_date(self, value: str) -> date | None:
        value = value.strip()
        if not value:
            return None
        try:
            return parse_date(value)
        except ValueError:
            QMessageBox.warning(self, "Filtro", "Use datas de filtro no formato mm-dd-aaaa.")
            return None

    def _filter_status(self) -> AppointmentStatus | None:
        if self.status_filter.currentText() == "Todos":
            return None
        return AppointmentStatus(self.status_filter.currentText())

    def _status_color(self, status: AppointmentStatus) -> QColor:
        colors = {
            AppointmentStatus.SCHEDULED: QColor("#d9f0df"),
            AppointmentStatus.CONFIRMED: QColor("#dbeafe"),
            AppointmentStatus.COMPLETED: QColor("#dcfce7"),
            AppointmentStatus.CANCELED: QColor("#fee2e2"),
            AppointmentStatus.PENDING: QColor("#fef3c7"),
        }
        return colors.get(status, QColor("#eef1f4"))

    def _audit(self, action: str, appointment_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="consultas",
            entity_id=appointment_id,
            details=details,
        )
