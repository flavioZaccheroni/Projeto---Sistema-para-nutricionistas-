from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QWidget,
)

from nutri_app.domain.screening import Screening, ScreeningProtocol
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.screening_repository import ScreeningRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.screening import ScreeningService
from nutri_app.ui.pages.base import Page


class ScreeningPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Triagem Nutricional", "Protocolos e classificacao automatica de risco.")
        self.repository = ScreeningRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = ScreeningService()
        self.selected_screening_id: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.protocol = QComboBox()
        self.protocol.addItems([protocol.value for protocol in ScreeningProtocol])
        self.score = QLineEdit()
        self.score.setPlaceholderText("Pontuacao")
        self.classification = QLineEdit()
        self.classification.setReadOnly(True)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(75)

        calculate = QPushButton("Calcular classificacao")
        calculate.clicked.connect(self._calculate_classification)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_screening)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_screening)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Consulta vinculada", self.appointment)
        form.addRow("Protocolo", self.protocol)
        form.addRow("Pontuacao", self.score)
        form.addRow("Classificacao", self.classification)
        form.addRow("Observacoes", self.notes)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Consulta", "Protocolo", "Pontuacao", "Classificacao", "Observacoes"]
        )
        self.table.cellClicked.connect(self._select_screening_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_table()

    def _save_screening(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Triagem", "Cadastre um paciente antes de criar triagem.")
            return

        try:
            score = float(self.score.text().replace(",", "."))
            protocol = ScreeningProtocol(self.protocol.currentText())
            classification = self.service.classify(protocol, score)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Pontuacao invalida.")
            return

        self.classification.setText(classification)
        screening = Screening(
            id=self.selected_screening_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            protocol=protocol,
            score=score,
            classification=classification,
            notes=self.notes.toPlainText().strip(),
        )

        if screening.id is None:
            screening_id = self.repository.add(screening)
            self._audit("criou_triagem", screening_id, "Triagem criada.")
        else:
            self.repository.update(screening)
            screening_id = screening.id
            self._audit("atualizou_triagem", screening_id, "Triagem atualizada.")

        self._clear_form()
        self._reload_table()

    def _calculate_classification(self) -> None:
        try:
            score = float(self.score.text().replace(",", "."))
            classification = self.service.classify(ScreeningProtocol(self.protocol.currentText()), score)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Pontuacao invalida.")
            return
        self.classification.setText(classification)

    def _delete_screening(self) -> None:
        if self.selected_screening_id is None:
            QMessageBox.warning(self, "Triagem", "Selecione uma triagem para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir triagem",
            "Deseja excluir esta triagem? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        screening_id = self.selected_screening_id
        self.repository.soft_delete(screening_id)
        self._audit("excluiu_triagem", screening_id, "Triagem removida por exclusao logica.")
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_screening_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        self.protocol.setCurrentIndex(0)
        self.score.clear()
        self.classification.clear()
        self.notes.clear()

    def _reload_patients(self) -> None:
        current_patient_id = None
        if self.patient.currentIndex() >= 0 and self.patient_ids_by_index:
            current_patient_id = self.patient_ids_by_index[self.patient.currentIndex()]

        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is None:
                continue
            self.patient.addItem(patient.name)
            self.patient_ids_by_index.append(patient.id)
        if current_patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_patient_id))
        self.patient.blockSignals(False)
        self._reload_appointments()

    def _reload_appointments(self) -> None:
        self.appointment.clear()
        self.appointment.addItem("Sem consulta vinculada")
        self.appointment_ids_by_index = [None]
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            return

        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        for appointment in self.appointment_repository.list_by_period():
            if appointment.patient_id != patient_id or appointment.id is None:
                continue
            self.appointment.addItem(
                f"{appointment.scheduled_at:%Y-%m-%d %H:%M} - {appointment.kind.value}"
            )
            self.appointment_ids_by_index.append(appointment.id)

    def _reload_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.patient_name))
            self.table.setItem(row, 2, QTableWidgetItem(record.appointment_label))
            self.table.setItem(row, 3, QTableWidgetItem(record.protocol.value))
            self.table.setItem(row, 4, QTableWidgetItem(str(record.score)))
            self.table.setItem(row, 5, QTableWidgetItem(record.classification))
            self.table.setItem(row, 6, QTableWidgetItem(record.notes))

    def _select_screening_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Triagem", "Registro nao encontrado.")
            self._reload_table()
            return

        self.selected_screening_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.protocol.setCurrentText(record.protocol.value)
        self.score.setText(str(record.score))
        self.classification.setText(record.classification)
        self.notes.setPlainText(record.notes)

    def _audit(self, action: str, screening_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="triagens",
            entity_id=screening_id,
            details=details,
        )
