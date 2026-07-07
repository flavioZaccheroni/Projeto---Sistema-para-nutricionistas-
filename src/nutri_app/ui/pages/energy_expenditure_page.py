from __future__ import annotations

from datetime import date

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

from nutri_app.domain.energy_expenditure import (
    BiologicalSex,
    EnergyEquation,
    EnergyExpenditure,
)
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.energy_expenditure_repository import EnergyExpenditureRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.energy_expenditure import EnergyExpenditureService
from nutri_app.ui.date_format import format_date, format_datetime, parse_date
from nutri_app.ui.pages.base import Page


class EnergyExpenditurePage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Gasto Energetico", "TMB, GET e necessidades nutricionais.")
        self.repository = EnergyExpenditureRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = EnergyExpenditureService()
        self.selected_expenditure_id: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.patient_records_by_index: list[Patient] = []
        self.appointment_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._patient_changed)
        self.appointment = QComboBox()
        self.assessment_date = QLineEdit()
        self.assessment_date.setPlaceholderText("mm-dd-aaaa")
        self.sex = QComboBox()
        self.sex.addItems([item.value for item in BiologicalSex])
        self.age = QLineEdit()
        self.weight = QLineEdit()
        self.height = QLineEdit()
        self.lean_mass = QLineEdit()
        self.equation = QComboBox()
        self.equation.addItems([item.value for item in EnergyEquation])
        self.activity_factor = QLineEdit("1.30")
        self.stress_factor = QLineEdit("1.00")
        self.goal_adjustment = QLineEdit("0")
        self.protein_per_kg = QLineEdit("1.20")
        self.fat_percentage = QLineEdit("30")
        self.basal_energy = QLineEdit()
        self.basal_energy.setReadOnly(True)
        self.total_energy = QLineEdit()
        self.total_energy.setReadOnly(True)
        self.protein = QLineEdit()
        self.protein.setReadOnly(True)
        self.carbohydrate = QLineEdit()
        self.carbohydrate.setReadOnly(True)
        self.fat = QLineEdit()
        self.fat.setReadOnly(True)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Consulta vinculada", self.appointment)
        form.addRow("Data da avaliacao", self.assessment_date)
        form.addRow("Sexo", self.sex)
        form.addRow("Idade (anos)", self.age)
        form.addRow("Peso (kg)", self.weight)
        form.addRow("Altura (cm)", self.height)
        form.addRow("Massa magra (kg)", self.lean_mass)
        form.addRow("Equacao", self.equation)
        form.addRow("Fator atividade", self.activity_factor)
        form.addRow("Fator estresse", self.stress_factor)
        form.addRow("Ajuste objetivo (kcal)", self.goal_adjustment)
        form.addRow("Proteina (g/kg)", self.protein_per_kg)
        form.addRow("Lipidios (%)", self.fat_percentage)
        form.addRow("TMB/EER (kcal)", self.basal_energy)
        form.addRow("GET (kcal)", self.total_energy)
        form.addRow("Proteina (g)", self.protein)
        form.addRow("Carboidrato (g)", self.carbohydrate)
        form.addRow("Lipidios (g)", self.fat)
        form.addRow("Observacoes", self.notes)

        calculate = QPushButton("Calcular")
        calculate.clicked.connect(self._calculate)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_expenditure)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_expenditure)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Data", "Equacao", "Peso", "TMB/EER", "GET", "Proteina"]
        )
        self.table.cellClicked.connect(self._select_expenditure_from_table)

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

    def _save_expenditure(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(
                self,
                "Gasto energetico",
                "Cadastre um paciente antes da avaliacao.",
            )
            return

        try:
            expenditure = self._build_expenditure()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if expenditure.id is None:
            expenditure_id = self.repository.add(expenditure)
            self._audit("criou_gasto_energetico", expenditure_id, "Gasto energetico criado.")
        else:
            self.repository.update(expenditure)
            expenditure_id = expenditure.id
            self._audit(
                "atualizou_gasto_energetico",
                expenditure_id,
                "Gasto energetico atualizado.",
            )

        self._clear_form()
        self._reload_table()

    def _build_expenditure(self) -> EnergyExpenditure:
        assessment_date = parse_date(self.assessment_date.text())
        sex = BiologicalSex(self.sex.currentText())
        age_years = self._required_int(self.age.text(), "Idade")
        weight = self._required_float(self.weight.text(), "Peso")
        height = self._required_float(self.height.text(), "Altura")
        lean_mass = self._optional_float(self.lean_mass.text(), "Massa magra")
        equation = EnergyEquation(self.equation.currentText())
        activity_factor = self._required_float(self.activity_factor.text(), "Fator atividade")
        stress_factor = self._required_float(self.stress_factor.text(), "Fator estresse")
        adjustment = self._optional_float_allow_zero(self.goal_adjustment.text(), "Ajuste objetivo")
        protein_per_kg = self._required_float(self.protein_per_kg.text(), "Proteina por kg")
        fat_percentage = self._optional_float_allow_zero(self.fat_percentage.text(), "Lipidios")

        basal = self.service.calculate_basal_energy(
            equation=equation,
            sex=sex,
            age_years=age_years,
            weight_kg=weight,
            height_cm=height,
            lean_mass_kg=lean_mass,
            activity_factor=activity_factor,
        )
        total = self.service.calculate_total_energy(
            basal_energy_kcal=basal,
            activity_factor=activity_factor,
            stress_factor=stress_factor,
            goal_adjustment_kcal=adjustment,
            equation=equation,
        )
        macros = self.service.calculate_macronutrients(
            total_energy_kcal=total,
            weight_kg=weight,
            protein_g_per_kg=protein_per_kg,
            fat_percentage=fat_percentage,
        )
        self._show_results(basal, total, macros.protein_g, macros.carbohydrate_g, macros.fat_g)

        return EnergyExpenditure(
            id=self.selected_expenditure_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            assessment_date=assessment_date,
            sex=sex,
            age_years=age_years,
            weight_kg=weight,
            height_cm=height,
            lean_mass_kg=lean_mass,
            equation=equation,
            activity_factor=activity_factor,
            stress_factor=stress_factor,
            goal_adjustment_kcal=adjustment,
            basal_energy_kcal=basal,
            total_energy_kcal=total,
            protein_g=macros.protein_g,
            carbohydrate_g=macros.carbohydrate_g,
            fat_g=macros.fat_g,
            notes=self.notes.toPlainText().strip(),
        )

    def _calculate(self) -> None:
        try:
            self._build_expenditure()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")

    def _delete_expenditure(self) -> None:
        if self.selected_expenditure_id is None:
            QMessageBox.warning(self, "Gasto energetico", "Selecione um registro para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir gasto energetico",
            "Deseja excluir esta avaliacao? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        expenditure_id = self.selected_expenditure_id
        self.repository.soft_delete(expenditure_id)
        self._audit(
            "excluiu_gasto_energetico",
            expenditure_id,
            "Gasto energetico removido por exclusao logica.",
        )
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_expenditure_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        self.sex.setCurrentIndex(0)
        self.equation.setCurrentIndex(0)
        self.activity_factor.setText("1.30")
        self.stress_factor.setText("1.00")
        self.goal_adjustment.setText("0")
        self.protein_per_kg.setText("1.20")
        self.fat_percentage.setText("30")
        for field in [
            self.assessment_date,
            self.age,
            self.weight,
            self.height,
            self.lean_mass,
            self.basal_energy,
            self.total_energy,
            self.protein,
            self.carbohydrate,
            self.fat,
        ]:
            field.clear()
        self.notes.clear()
        self._fill_age_from_patient()

    def _reload_patients(self) -> None:
        current_patient_id = None
        if self.patient.currentIndex() >= 0 and self.patient_ids_by_index:
            current_patient_id = self.patient_ids_by_index[self.patient.currentIndex()]

        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = []
        self.patient_records_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is None:
                continue
            self.patient.addItem(patient.name)
            self.patient_ids_by_index.append(patient.id)
            self.patient_records_by_index.append(patient)
        if current_patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_patient_id))
        self.patient.blockSignals(False)
        self._patient_changed()

    def _patient_changed(self) -> None:
        self._reload_appointments()
        self._fill_age_from_patient()

    def _fill_age_from_patient(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_records_by_index:
            return
        if self.age.text().strip():
            return
        patient = self.patient_records_by_index[self.patient.currentIndex()]
        today = date.today()
        age = today.year - patient.birth_date.year
        if (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day):
            age -= 1
        self.age.setText(str(max(age, 1)))

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
            self.table.setItem(row, 3, QTableWidgetItem(record.equation.value))
            self.table.setItem(row, 4, QTableWidgetItem(f"{record.weight_kg:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{record.basal_energy_kcal:.0f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{record.total_energy_kcal:.0f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{record.protein_g:.1f}"))

    def _select_expenditure_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Gasto energetico", "Registro nao encontrado.")
            self._reload_table()
            return

        self.selected_expenditure_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.assessment_date.setText(format_date(record.assessment_date))
        self.sex.setCurrentText(record.sex.value)
        self.age.setText(str(record.age_years))
        self.weight.setText(str(record.weight_kg))
        self.height.setText(str(record.height_cm))
        self.lean_mass.setText(self._format_optional(record.lean_mass_kg))
        self.equation.setCurrentText(record.equation.value)
        self.activity_factor.setText(str(record.activity_factor))
        self.stress_factor.setText(str(record.stress_factor))
        self.goal_adjustment.setText(str(record.goal_adjustment_kcal))
        self._show_results(
            record.basal_energy_kcal,
            record.total_energy_kcal,
            record.protein_g,
            record.carbohydrate_g,
            record.fat_g,
        )
        self.notes.setPlainText(record.notes)

    def _show_results(
        self,
        basal: float,
        total: float,
        protein: float,
        carbohydrate: float,
        fat: float,
    ) -> None:
        self.basal_energy.setText(f"{basal:.0f}")
        self.total_energy.setText(f"{total:.0f}")
        self.protein.setText(f"{protein:.1f}")
        self.carbohydrate.setText(f"{carbohydrate:.1f}")
        self.fat.setText(f"{fat:.1f}")

    def _required_int(self, value: str, label: str) -> int:
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc
        if parsed <= 0:
            raise ValueError(f"{label} deve ser maior que zero.")
        return parsed

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

    def _optional_float_allow_zero(self, value: str, label: str) -> float:
        if not value.strip():
            return 0
        try:
            return float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc

    def _format_optional(self, value: float | None) -> str:
        return "" if value is None else f"{value:.2f}"

    def _audit(self, action: str, expenditure_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="gastos_energeticos",
            entity_id=expenditure_id,
            details=details,
        )
