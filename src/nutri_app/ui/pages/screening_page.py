from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nutri_app.domain.screening import Screening, ScreeningProtocol
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.screening_repository import ScreeningRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.screening import ScreeningService
from nutri_app.ui.date_format import format_date, format_datetime, today_text
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
        self.assessment_date = QLineEdit(today_text())
        self.assessment_date.setPlaceholderText("mm-dd-aaaa")
        self.score = QLineEdit()
        self.score.setPlaceholderText("Pontuacao")
        self.classification = QLineEdit()
        self.classification.setReadOnly(True)
        self.risk_meter = QProgressBar()
        self.risk_meter.setRange(0, 100)
        self.risk_meter.setTextVisible(False)
        self.risk_meter.setValue(0)
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

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Paciente",
                "Consulta",
                "Protocolo",
                "Pontuacao",
                "Classificacao",
                "Observacoes",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._select_screening_from_table)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(12)
        wrapper_layout.addWidget(self._build_identity_card())
        wrapper_layout.addWidget(self._build_assessment_card())
        wrapper_layout.addWidget(self._build_results_card())
        wrapper_layout.addLayout(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def _build_identity_card(self) -> QGroupBox:
        card = QGroupBox("Pesquisa e Identificacao")
        layout = QGridLayout(card)
        avatar = QLabel("NC")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(44, 44)
        avatar.setObjectName("avatarBadge")
        layout.addWidget(avatar, 0, 0, 2, 1)
        self._add_stacked_field(layout, 0, "Paciente", self.patient, column=1)
        self._add_stacked_field(layout, 0, "Pesquisar", self.search, column=3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        return card

    def _build_assessment_card(self) -> QGroupBox:
        card = QGroupBox("Informacoes da Avaliacao")
        layout = QGridLayout(card)
        self._add_icon_badge(layout, 0, 0, "Consulta")
        self._add_stacked_field(layout, 0, "Consulta vinculada", self.appointment, column=1)
        self._add_icon_badge(layout, 0, 3, "Protocolo")
        self._add_stacked_field(layout, 0, "Protocolo", self.protocol, column=4)
        self._add_icon_badge(layout, 0, 6, "Data")
        self._add_stacked_field(layout, 0, "Data da avaliacao", self.assessment_date, column=7)
        for column in [1, 4, 7]:
            layout.setColumnStretch(column, 1)
        return card

    def _build_results_card(self) -> QGroupBox:
        card = QGroupBox("Resultados e Notas")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Pontuacao", self.score)
        self._add_stacked_field(layout, 0, "Classificacao", self.classification, column=2)
        layout.addWidget(self.risk_meter, 1, 4)
        self._add_stacked_field(layout, 0, "Observacoes", self.notes, column=5)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(4, 1)
        layout.setColumnStretch(5, 1)
        return card

    def _add_stacked_field(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        widget: QWidget,
        column: int = 0,
        column_span: int = 1,
    ) -> None:
        title = QLabel(label)
        title.setObjectName("miniHeader")
        layout.addWidget(title, row, column, 1, column_span)
        layout.addWidget(widget, row + 1, column, 1, column_span)

    def _add_icon_badge(self, layout: QGridLayout, row: int, column: int, label: str) -> None:
        badge = QLabel(label[:1])
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(38, 38)
        badge.setObjectName("softIconBadge")
        layout.addWidget(badge, row + 1, column)

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
        self._refresh_risk_meter(classification)
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
            classification = self.service.classify(
                ScreeningProtocol(self.protocol.currentText()),
                score,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Pontuacao invalida.")
            return
        self.classification.setText(classification)
        self._refresh_risk_meter(classification)

    def _refresh_risk_meter(self, classification: str) -> None:
        normalized = classification.lower()
        if not normalized:
            self.risk_meter.setValue(0)
            return
        if "grave" in normalized or "alto" in normalized or "desnutricao" in normalized:
            self.risk_meter.setValue(90)
            return
        if "risco" in normalized or "medio" in normalized or "moderada" in normalized:
            self.risk_meter.setValue(60)
            return
        self.risk_meter.setValue(25)

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
        self.assessment_date.setText(today_text())
        self.risk_meter.setValue(0)
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
                f"{format_datetime(appointment.scheduled_at)} - {appointment.kind.value}"
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
        if record.created_at is not None:
            self.assessment_date.setText(format_date(record.created_at.date()))
        self._refresh_risk_meter(record.classification)
        self.notes.setPlainText(record.notes)

    def _audit(self, action: str, screening_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="triagens",
            entity_id=screening_id,
            details=details,
        )
