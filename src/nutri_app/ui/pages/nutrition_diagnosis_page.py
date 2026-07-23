from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
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
    QWidget,
)

from nutri_app.domain.nutrition_diagnosis import DiagnosisProtocol, NutritionDiagnosis
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.nutrition_diagnosis_repository import NutritionDiagnosisRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.nutrition_diagnosis import NutritionDiagnosisService
from nutri_app.ui.date_format import format_date, format_datetime, parse_date
from nutri_app.ui.pages.base import Page


class NutritionDiagnosisPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Diagnostico Nutricional", "Classificacao por protocolos clinicos.")
        self.repository = NutritionDiagnosisRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = NutritionDiagnosisService()
        self.selected_diagnosis_id: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.diagnosis_date = QLineEdit()
        self.diagnosis_date.setPlaceholderText("mm-dd-aaaa")
        self.protocol = QComboBox()
        self.protocol.addItems([protocol.value for protocol in DiagnosisProtocol])
        self.primary_label = QLineEdit("Criterios principais/fenotipicos")
        self.primary_count = QLineEdit("0")
        self.secondary_label = QLineEdit("Criterios secundarios/etiologicos")
        self.secondary_count = QLineEdit("0")
        self.severe_marker = QCheckBox("Marcador de gravidade")
        self.confirmed = QCheckBox("Confirmado pela nutricionista")
        self.classification = QLineEdit()
        self.classification.setReadOnly(True)
        self.severity = QLineEdit()
        self.severity.setReadOnly(True)
        self.criteria = QTextEdit()
        self.criteria.setFixedHeight(55)
        self.criteria.setReadOnly(True)
        self.criteria.setPlaceholderText("Criterios registrados")
        self.conduct = QTextEdit()
        self.conduct.setFixedHeight(82)
        self.conduct.setPlaceholderText("Conduta")
        self.notes = QTextEdit()
        self.notes.setFixedHeight(82)
        self.notes.setPlaceholderText("Observacoes")

        calculate = QPushButton("Classificar")
        calculate.clicked.connect(self._calculate)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_diagnosis)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_diagnosis)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Paciente",
                "Data",
                "Protocolo",
                "Classificacao",
                "Gravidade",
                "Confirmado",
            ]
        )
        self.table.cellClicked.connect(self._select_diagnosis_from_table)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        cards = QWidget()
        cards_layout = QGridLayout(cards)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setHorizontalSpacing(14)
        cards_layout.addWidget(self._patient_card(), 0, 0)
        cards_layout.addWidget(self._protocol_card(), 0, 1)
        cards_layout.addWidget(self._results_card(), 0, 2)
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        cards_layout.setColumnStretch(2, 1)

        self.layout.addWidget(cards)
        self.layout.addLayout(actions)
        self.layout.addWidget(self.table)
        self.refresh()

    def _patient_card(self) -> QGroupBox:
        card = QGroupBox("Informacoes do Paciente")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Pesquisar", self.search)
        self._add_stacked_field(layout, 2, "Paciente", self.patient)
        self._add_stacked_field(layout, 4, "Consulta vinculada", self.appointment)
        self._add_stacked_field(layout, 6, "Data do diagnostico", self.diagnosis_date)
        layout.setColumnStretch(1, 1)
        return card

    def _protocol_card(self) -> QGroupBox:
        card = QGroupBox("Protocolo e Criterios")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Protocolo", self.protocol)
        self._add_stacked_field(layout, 2, "Grupo criterio 1", self.primary_label)
        self._add_stacked_field(layout, 4, "Quantidade criterio 1", self.primary_count)
        self._add_stacked_field(layout, 6, "Grupo criterio 2", self.secondary_label)
        self._add_stacked_field(layout, 8, "Quantidade criterio 2", self.secondary_count)
        layout.setColumnStretch(1, 1)
        return card

    def _results_card(self) -> QGroupBox:
        card = QGroupBox("Resultados e Notas")
        layout = QGridLayout(card)
        layout.addWidget(QLabel("Gravidade"), 0, 0)
        layout.addWidget(self.severe_marker, 0, 1)
        layout.addWidget(QLabel("Confirmacao"), 1, 0)
        layout.addWidget(self.confirmed, 1, 1)
        self._add_stacked_field(layout, 2, "Classificacao", self.classification)
        self._add_stacked_field(layout, 4, "Gravidade sugerida", self.severity)
        self._add_stacked_field(layout, 6, "Criterios registrados", self.criteria)
        self._add_stacked_field(layout, 8, "Conduta", self.conduct)
        self._add_stacked_field(layout, 10, "Observacoes", self.notes)
        layout.setColumnStretch(1, 1)
        return card

    def _add_stacked_field(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        widget: QWidget,
    ) -> None:
        title = QLabel(label)
        title.setObjectName("miniHeader")
        layout.addWidget(title, row, 0, 1, 2)
        layout.addWidget(widget, row + 1, 0, 1, 2)

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_table()

    def _save_diagnosis(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Diagnostico", "Cadastre um paciente antes do diagnostico.")
            return

        try:
            diagnosis = self._build_diagnosis()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if diagnosis.id is None:
            diagnosis_id = self.repository.add(diagnosis)
            self._audit("criou_diagnostico_nutricional", diagnosis_id, "Diagnostico criado.")
        else:
            self.repository.update(diagnosis)
            diagnosis_id = diagnosis.id
            self._audit(
                "atualizou_diagnostico_nutricional",
                diagnosis_id,
                "Diagnostico atualizado.",
            )

        self._clear_form()
        self._reload_table()

    def _build_diagnosis(self) -> NutritionDiagnosis:
        diagnosis_date = parse_date(self.diagnosis_date.text())
        protocol = DiagnosisProtocol(self.protocol.currentText())
        primary_count = self._required_int(self.primary_count.text(), "Quantidade criterio 1")
        secondary_count = self._required_int(self.secondary_count.text(), "Quantidade criterio 2")
        classification, severity = self.service.classify(
            protocol,
            primary_count,
            secondary_count,
            self.severe_marker.isChecked(),
        )
        criteria = self.service.build_criteria_text(
            self.primary_label.text().strip() or "Criterio 1",
            primary_count,
            self.secondary_label.text().strip() or "Criterio 2",
            secondary_count,
            self.severe_marker.isChecked(),
        )
        self._show_results(classification, severity.value, criteria)
        return NutritionDiagnosis(
            id=self.selected_diagnosis_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            diagnosis_date=diagnosis_date,
            protocol=protocol,
            criteria=criteria,
            classification=classification,
            severity=severity,
            confirmed=self.confirmed.isChecked(),
            conduct=self.conduct.toPlainText().strip(),
            notes=self.notes.toPlainText().strip(),
        )

    def _calculate(self) -> None:
        try:
            self._build_diagnosis()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")

    def _delete_diagnosis(self) -> None:
        if self.selected_diagnosis_id is None:
            QMessageBox.warning(self, "Diagnostico", "Selecione um diagnostico para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir diagnostico",
            "Deseja excluir este diagnostico? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        diagnosis_id = self.selected_diagnosis_id
        self.repository.soft_delete(diagnosis_id)
        self._audit(
            "excluiu_diagnostico_nutricional",
            diagnosis_id,
            "Diagnostico removido por exclusao logica.",
        )
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_diagnosis_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        self.protocol.setCurrentIndex(0)
        self.primary_label.setText("Criterios principais/fenotipicos")
        self.primary_count.setText("0")
        self.secondary_label.setText("Criterios secundarios/etiologicos")
        self.secondary_count.setText("0")
        self.severe_marker.setChecked(False)
        self.confirmed.setChecked(False)
        for field in [self.diagnosis_date, self.classification, self.severity]:
            field.clear()
        for field in [self.criteria, self.conduct, self.notes]:
            field.clear()

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
            self.table.setItem(row, 2, QTableWidgetItem(format_date(record.diagnosis_date)))
            self.table.setItem(row, 3, QTableWidgetItem(record.protocol.value))
            self.table.setItem(row, 4, QTableWidgetItem(record.classification))
            self.table.setItem(row, 5, QTableWidgetItem(record.severity.value))
            self.table.setItem(row, 6, QTableWidgetItem("sim" if record.confirmed else "nao"))

    def _select_diagnosis_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Diagnostico", "Diagnostico nao encontrado.")
            self._reload_table()
            return

        self.selected_diagnosis_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.diagnosis_date.setText(format_date(record.diagnosis_date))
        self.protocol.setCurrentText(record.protocol.value)
        self.criteria.setPlainText(record.criteria)
        self.classification.setText(record.classification)
        self.severity.setText(record.severity.value)
        self.confirmed.setChecked(record.confirmed)
        self.conduct.setPlainText(record.conduct)
        self.notes.setPlainText(record.notes)

    def _show_results(self, classification: str, severity: str, criteria: str) -> None:
        self.classification.setText(classification)
        self.severity.setText(severity)
        self.criteria.setPlainText(criteria)

    def _required_int(self, value: str, label: str) -> int:
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc
        if parsed < 0:
            raise ValueError(f"{label} nao pode ser negativo.")
        return parsed

    def _audit(self, action: str, diagnosis_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="diagnosticos_nutricionais",
            entity_id=diagnosis_id,
            details=details,
        )
