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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.domain.anthropometry import Anthropometry
from nutri_app.repositories.advanced_clinical_repository import AdvancedClinicalRepository
from nutri_app.repositories.anthropometry_repository import AnthropometryRepository
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.services.anthropometry import AnthropometryService
from nutri_app.ui.date_format import (
    format_date,
    format_datetime,
    parse_date,
    today_text,
)
from nutri_app.ui.pages.base import Page


class AnthropometryPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Antropometria", "Medidas corporais e indicadores automaticos.")
        self.repository = AnthropometryRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.advanced_repository = AdvancedClinicalRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = AnthropometryService()
        self.advanced_definition = AdvancedClinicalService().by_module("Antropometria Avancada")
        self.selected_anthropometry_id: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []
        self.advanced_patient_ids_by_index: list[int | None] = []
        self.advanced_inputs: dict[str, QLineEdit] = {}

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.assessment_date = QLineEdit()
        self.assessment_date.setPlaceholderText("mm-dd-aaaa")
        self.weight = QLineEdit()
        self.height = QLineEdit()
        self.waist = QLineEdit()
        self.hip = QLineEdit()
        self.bmi = QLineEdit()
        self.bmi.setReadOnly(True)
        self.bmi_classification = QLineEdit()
        self.bmi_classification.setReadOnly(True)
        self.waist_hip_ratio = QLineEdit()
        self.waist_hip_ratio.setReadOnly(True)
        self.waist_height_ratio = QLineEdit()
        self.waist_height_ratio.setReadOnly(True)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Consulta vinculada", self.appointment)
        form.addRow("Data da avaliacao", self.assessment_date)
        form.addRow("Peso (kg)", self.weight)
        form.addRow("Altura (m)", self.height)
        form.addRow("Cintura (cm)", self.waist)
        form.addRow("Quadril (cm)", self.hip)
        form.addRow("IMC", self.bmi)
        form.addRow("Classificacao IMC", self.bmi_classification)
        form.addRow("RCQ", self.waist_hip_ratio)
        form.addRow("RCEst", self.waist_height_ratio)
        form.addRow("Observacoes", self.notes)

        calculate = QPushButton("Calcular")
        calculate.clicked.connect(self._calculate_indicators)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_anthropometry)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_anthropometry)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Data", "Peso", "Altura", "IMC", "Classificacao", "RCQ", "RCEst"]
        )
        self.table.cellClicked.connect(self._select_anthropometry_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.addWidget(wrapper)
        basic_layout.addWidget(self.table)

        tabs = QTabWidget()
        tabs.addTab(basic_tab, "Basica")
        tabs.addTab(self._build_advanced_tab(), "Avancada")

        self.layout.addWidget(tabs)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_table()
        self._reload_advanced_patients()
        self._reload_advanced_table()

    def _build_advanced_tab(self) -> QWidget:
        self.advanced_patient = QComboBox()
        self.advanced_record_date = QLineEdit(today_text())
        self.advanced_record_date.setPlaceholderText("mm-dd-aaaa")
        self.advanced_profile = QComboBox()
        self.advanced_profile.addItems(self.advanced_definition.profiles)
        self.advanced_notes = QTextEdit()
        self.advanced_notes.setFixedHeight(70)
        self.advanced_result = QTextEdit()
        self.advanced_result.setReadOnly(True)
        self.advanced_result.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Paciente", self.advanced_patient)
        form.addRow("Data da avaliacao", self.advanced_record_date)
        form.addRow("Perfil", self.advanced_profile)
        for key, label in self.advanced_definition.fields:
            field = QLineEdit()
            self.advanced_inputs[key] = field
            form.addRow(label, field)
        form.addRow("Observacoes", self.advanced_notes)
        form.addRow("Resultado", self.advanced_result)

        calculate = QPushButton("Calcular / salvar")
        calculate.setObjectName("primaryButton")
        calculate.clicked.connect(self._save_advanced_anthropometry)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self._clear_advanced_form)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self._reload_advanced_table)

        actions = QHBoxLayout()
        for button in [calculate, clear, refresh]:
            actions.addWidget(button)
        actions.addStretch()

        self.advanced_table = QTableWidget(0, 6)
        self.advanced_table.setHorizontalHeaderLabels(
            ["ID", "Data", "Paciente", "Perfil", "Resultado", "Observacoes"]
        )

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(wrapper)
        layout.addWidget(self.advanced_table)
        return tab

    def _save_anthropometry(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Antropometria", "Cadastre um paciente antes da avaliacao.")
            return

        try:
            anthropometry = self._build_anthropometry()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if anthropometry.id is None:
            anthropometry_id = self.repository.add(anthropometry)
            self._audit("criou_antropometria", anthropometry_id, "Avaliacao antropometrica criada.")
        else:
            self.repository.update(anthropometry)
            anthropometry_id = anthropometry.id
            self._audit(
                "atualizou_antropometria",
                anthropometry_id,
                "Avaliacao antropometrica atualizada.",
            )

        self._clear_form()
        self._reload_table()

    def _build_anthropometry(self) -> Anthropometry:
        assessment_date = parse_date(self.assessment_date.text())
        weight = self._required_float(self.weight.text(), "Peso")
        height = self._required_float(self.height.text(), "Altura")
        waist = self._optional_float(self.waist.text(), "Cintura")
        hip = self._optional_float(self.hip.text(), "Quadril")

        bmi = self.service.calculate_bmi(weight, height)
        classification = self.service.classify_adult_bmi(bmi).value
        waist_hip_ratio = None
        waist_height_ratio = None
        if waist is not None and hip is not None:
            waist_hip_ratio = self.service.calculate_waist_hip_ratio(waist, hip)
        if waist is not None:
            waist_height_ratio = self.service.calculate_waist_height_ratio(waist, height)

        self._show_results(bmi, classification, waist_hip_ratio, waist_height_ratio)
        return Anthropometry(
            id=self.selected_anthropometry_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            assessment_date=assessment_date,
            weight_kg=weight,
            height_m=height,
            bmi=bmi,
            bmi_classification=classification,
            waist_cm=waist,
            hip_cm=hip,
            waist_hip_ratio=waist_hip_ratio,
            waist_height_ratio=waist_height_ratio,
            notes=self.notes.toPlainText().strip(),
        )

    def _calculate_indicators(self) -> None:
        try:
            self._build_anthropometry()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")

    def _delete_anthropometry(self) -> None:
        if self.selected_anthropometry_id is None:
            QMessageBox.warning(self, "Antropometria", "Selecione uma avaliacao para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir antropometria",
            "Deseja excluir esta avaliacao? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        anthropometry_id = self.selected_anthropometry_id
        self.repository.soft_delete(anthropometry_id)
        self._audit(
            "excluiu_antropometria",
            anthropometry_id,
            "Avaliacao removida por exclusao logica.",
        )
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_anthropometry_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        for field in [
            self.assessment_date,
            self.weight,
            self.height,
            self.waist,
            self.hip,
            self.bmi,
            self.bmi_classification,
            self.waist_hip_ratio,
            self.waist_height_ratio,
        ]:
            field.clear()
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
            self.table.setItem(row, 2, QTableWidgetItem(format_date(record.assessment_date)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{record.weight_kg:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{record.height_m:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{record.bmi:.1f}"))
            self.table.setItem(row, 6, QTableWidgetItem(record.bmi_classification))
            self.table.setItem(
                row,
                7,
                QTableWidgetItem(self._format_optional(record.waist_hip_ratio)),
            )
            self.table.setItem(
                row,
                8,
                QTableWidgetItem(self._format_optional(record.waist_height_ratio)),
            )

    def _save_advanced_anthropometry(self) -> None:
        if self.advanced_patient.currentIndex() < 0:
            QMessageBox.warning(self, "Antropometria", "Cadastre um paciente antes da avaliacao.")
            return

        try:
            record_date = parse_date(self.advanced_record_date.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Data invalida.")
            return

        profile = self.advanced_profile.currentText()
        inputs = {
            key: field.text().strip()
            for key, field in self.advanced_inputs.items()
        }
        notes = self.advanced_notes.toPlainText().strip()
        result = self.advanced_definition.evaluator(profile, inputs, notes)
        self.advanced_result.setPlainText(result)

        record = AdvancedClinicalRecord(
            module=self.advanced_definition.module,
            patient_id=self.advanced_patient_ids_by_index[self.advanced_patient.currentIndex()],
            record_date=record_date,
            profile=profile,
            inputs=inputs,
            result=result,
            notes=notes,
        )
        record_id = self.advanced_repository.add(record)
        self.audit_repository.log(
            user_id=self.current_user_id,
            action="registrou_antropometria_avancada",
            entity="registros_clinicos_avancados",
            entity_id=record_id,
            details="Avaliacao antropometrica avancada registrada.",
        )
        self._reload_advanced_table()
        QMessageBox.information(self, "Antropometria", "Avaliacao avancada registrada.")

    def _reload_advanced_patients(self) -> None:
        current_patient_id = None
        if self.advanced_patient.currentIndex() >= 0 and self.advanced_patient_ids_by_index:
            current_patient_id = self.advanced_patient_ids_by_index[
                self.advanced_patient.currentIndex()
            ]

        self.advanced_patient.clear()
        self.advanced_patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is None:
                continue
            self.advanced_patient.addItem(patient.name)
            self.advanced_patient_ids_by_index.append(patient.id)
        if current_patient_id in self.advanced_patient_ids_by_index:
            self.advanced_patient.setCurrentIndex(
                self.advanced_patient_ids_by_index.index(current_patient_id)
            )

    def _reload_advanced_table(self) -> None:
        records = self.advanced_repository.list_by_module(self.advanced_definition.module)
        self.advanced_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.advanced_table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.advanced_table.setItem(row, 1, QTableWidgetItem(format_date(record.record_date)))
            self.advanced_table.setItem(row, 2, QTableWidgetItem(record.patient_name))
            self.advanced_table.setItem(row, 3, QTableWidgetItem(record.profile))
            self.advanced_table.setItem(row, 4, QTableWidgetItem(record.result))
            self.advanced_table.setItem(row, 5, QTableWidgetItem(record.notes))

    def _clear_advanced_form(self) -> None:
        self.advanced_record_date.setText(today_text())
        if self.advanced_patient.count() > 0:
            self.advanced_patient.setCurrentIndex(0)
        if self.advanced_profile.count() > 0:
            self.advanced_profile.setCurrentIndex(0)
        for field in self.advanced_inputs.values():
            field.clear()
        self.advanced_notes.clear()
        self.advanced_result.clear()

    def _select_anthropometry_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Antropometria", "Avaliacao nao encontrada.")
            self._reload_table()
            return

        self.selected_anthropometry_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.assessment_date.setText(format_date(record.assessment_date))
        self.weight.setText(str(record.weight_kg))
        self.height.setText(str(record.height_m))
        self.waist.setText("" if record.waist_cm is None else str(record.waist_cm))
        self.hip.setText("" if record.hip_cm is None else str(record.hip_cm))
        self._show_results(
            record.bmi,
            record.bmi_classification,
            record.waist_hip_ratio,
            record.waist_height_ratio,
        )
        self.notes.setPlainText(record.notes)

    def _show_results(
        self,
        bmi: float,
        classification: str,
        waist_hip_ratio: float | None,
        waist_height_ratio: float | None,
    ) -> None:
        self.bmi.setText(f"{bmi:.1f}")
        self.bmi_classification.setText(classification)
        self.waist_hip_ratio.setText(self._format_optional(waist_hip_ratio))
        self.waist_height_ratio.setText(self._format_optional(waist_height_ratio))

    def _required_float(self, value: str, label: str) -> float:
        try:
            parsed = float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc
        if parsed <= 0:
            raise ValueError(f"{label} deve ser maior que zero.")
        return parsed

    def _optional_float(self, value: str, label: str) -> float | None:
        if not value.strip():
            return None
        return self._required_float(value, label)

    def _format_optional(self, value: float | None) -> str:
        return "" if value is None else f"{value:.2f}"

    def _audit(self, action: str, anthropometry_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="antropometrias",
            entity_id=anthropometry_id,
            details=details,
        )
