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

from nutri_app.domain.body_composition import BodyComposition, BodyCompositionProtocol
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.body_composition_repository import BodyCompositionRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.body_composition import BodyCompositionService
from nutri_app.ui.date_format import format_date, format_datetime, parse_date
from nutri_app.ui.pages.base import Page


class BodyCompositionPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Composicao Corporal", "Bioimpedancia, dobras e protocolos de composicao.")
        self.repository = BodyCompositionRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = BodyCompositionService()
        self.selected_composition_id: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.assessment_date = QLineEdit()
        self.assessment_date.setPlaceholderText("mm-dd-aaaa")
        self.protocol = QComboBox()
        self.protocol.addItems([protocol.value for protocol in BodyCompositionProtocol])
        self.weight = QLineEdit()
        self.body_fat_percentage = QLineEdit()
        self.fat_mass = QLineEdit()
        self.fat_mass.setReadOnly(True)
        self.lean_mass = QLineEdit()
        self.lean_mass.setReadOnly(True)
        self.body_water_percentage = QLineEdit()
        self.muscle_mass = QLineEdit()
        self.visceral_fat = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Consulta vinculada", self.appointment)
        form.addRow("Data da avaliacao", self.assessment_date)
        form.addRow("Protocolo", self.protocol)
        form.addRow("Peso (kg)", self.weight)
        form.addRow("% gordura", self.body_fat_percentage)
        form.addRow("Massa gorda (kg)", self.fat_mass)
        form.addRow("Massa magra (kg)", self.lean_mass)
        form.addRow("% agua corporal", self.body_water_percentage)
        form.addRow("Massa muscular (kg)", self.muscle_mass)
        form.addRow("Gordura visceral", self.visceral_fat)
        form.addRow("Observacoes", self.notes)

        calculate = QPushButton("Calcular")
        calculate.clicked.connect(self._calculate)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_composition)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_composition)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Data", "Protocolo", "Peso", "% gordura", "M. gorda", "M. magra"]
        )
        self.table.cellClicked.connect(self._select_composition_from_table)

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

    def _save_composition(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(
                self,
                "Composicao corporal",
                "Cadastre um paciente antes da avaliacao.",
            )
            return

        try:
            composition = self._build_composition()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if composition.id is None:
            composition_id = self.repository.add(composition)
            self._audit("criou_composicao_corporal", composition_id, "Composicao corporal criada.")
        else:
            self.repository.update(composition)
            composition_id = composition.id
            self._audit(
                "atualizou_composicao_corporal",
                composition_id,
                "Composicao corporal atualizada.",
            )

        self._clear_form()
        self._reload_table()

    def _build_composition(self) -> BodyComposition:
        assessment_date = parse_date(self.assessment_date.text())
        weight = self._required_float(self.weight.text(), "Peso")
        body_fat = self._required_float(self.body_fat_percentage.text(), "Percentual de gordura")
        fat_mass = self.service.calculate_fat_mass(weight, body_fat)
        lean_mass = self.service.calculate_lean_mass(weight, body_fat)
        self._show_results(fat_mass, lean_mass)

        return BodyComposition(
            id=self.selected_composition_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            assessment_date=assessment_date,
            protocol=BodyCompositionProtocol(self.protocol.currentText()),
            weight_kg=weight,
            body_fat_percentage=body_fat,
            fat_mass_kg=fat_mass,
            lean_mass_kg=lean_mass,
            body_water_percentage=self._optional_float(
                self.body_water_percentage.text(),
                "Agua corporal",
            ),
            muscle_mass_kg=self._optional_float(self.muscle_mass.text(), "Massa muscular"),
            visceral_fat=self._optional_float(self.visceral_fat.text(), "Gordura visceral"),
            notes=self.notes.toPlainText().strip(),
        )

    def _calculate(self) -> None:
        try:
            self._build_composition()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")

    def _delete_composition(self) -> None:
        if self.selected_composition_id is None:
            QMessageBox.warning(
                self,
                "Composicao corporal",
                "Selecione uma avaliacao para excluir.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir composicao corporal",
            "Deseja excluir esta avaliacao? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        composition_id = self.selected_composition_id
        self.repository.soft_delete(composition_id)
        self._audit(
            "excluiu_composicao_corporal",
            composition_id,
            "Composicao corporal removida por exclusao logica.",
        )
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_composition_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        self.protocol.setCurrentIndex(0)
        for field in [
            self.assessment_date,
            self.weight,
            self.body_fat_percentage,
            self.fat_mass,
            self.lean_mass,
            self.body_water_percentage,
            self.muscle_mass,
            self.visceral_fat,
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
            self.table.setItem(row, 3, QTableWidgetItem(record.protocol.value))
            self.table.setItem(row, 4, QTableWidgetItem(f"{record.weight_kg:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{record.body_fat_percentage:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{record.fat_mass_kg:.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{record.lean_mass_kg:.2f}"))

    def _select_composition_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Composicao corporal", "Avaliacao nao encontrada.")
            self._reload_table()
            return

        self.selected_composition_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.assessment_date.setText(format_date(record.assessment_date))
        self.protocol.setCurrentText(record.protocol.value)
        self.weight.setText(str(record.weight_kg))
        self.body_fat_percentage.setText(str(record.body_fat_percentage))
        self._show_results(record.fat_mass_kg, record.lean_mass_kg)
        self.body_water_percentage.setText(self._format_optional(record.body_water_percentage))
        self.muscle_mass.setText(self._format_optional(record.muscle_mass_kg))
        self.visceral_fat.setText(self._format_optional(record.visceral_fat))
        self.notes.setPlainText(record.notes)

    def _show_results(self, fat_mass: float, lean_mass: float) -> None:
        self.fat_mass.setText(f"{fat_mass:.2f}")
        self.lean_mass.setText(f"{lean_mass:.2f}")

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

    def _audit(self, action: str, composition_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="composicoes_corporais",
            entity_id=composition_id,
            details=details,
        )
