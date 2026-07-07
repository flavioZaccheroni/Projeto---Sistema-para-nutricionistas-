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

from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.repositories.advanced_clinical_repository import AdvancedClinicalRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedModuleDefinition
from nutri_app.ui.date_format import format_date, parse_date, today_text
from nutri_app.ui.pages.base import Page


class AdvancedModulePage(Page):
    def __init__(
        self,
        definition: AdvancedModuleDefinition,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(definition.title, f"Fase {definition.phase}: {definition.subtitle}")
        self.definition = definition
        self.repository = AdvancedClinicalRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.patient_ids: list[int | None] = []
        self.inputs: dict[str, QLineEdit] = {}

        self.patient = QComboBox()
        self.record_date = QLineEdit(today_text())
        self.record_date.setPlaceholderText("mm-dd-aaaa")
        self.profile = QComboBox()
        self.profile.addItems(definition.profiles)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Paciente", self.patient)
        form.addRow("Data", self.record_date)
        form.addRow("Perfil", self.profile)
        for key, label in definition.fields:
            field = QLineEdit()
            self.inputs[key] = field
            form.addRow(label, field)
        form.addRow("Observacoes", self.notes)
        form.addRow("Resultado", self.result)

        evaluate = QPushButton("Calcular / avaliar")
        evaluate.setObjectName("primaryButton")
        evaluate.clicked.connect(self._evaluate)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self._clear)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)

        actions = QHBoxLayout()
        actions.addWidget(evaluate)
        actions.addWidget(clear)
        actions.addWidget(refresh)
        actions.addStretch()

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data", "Paciente", "Perfil", "Resultado", "Obs."]
        )

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self._load_patients()
        records = self.repository.list_by_module(self.definition.module)
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(format_date(record.record_date)))
            self.table.setItem(row, 2, QTableWidgetItem(record.patient_name))
            self.table.setItem(row, 3, QTableWidgetItem(record.profile))
            self.table.setItem(row, 4, QTableWidgetItem(record.result))
            self.table.setItem(row, 5, QTableWidgetItem(record.notes))

    def _evaluate(self) -> None:
        try:
            values = {key: field.text().strip() for key, field in self.inputs.items()}
            notes = self.notes.toPlainText().strip()
            result = self.definition.evaluator(self.profile.currentText(), values, notes)
            record = AdvancedClinicalRecord(
                module=self.definition.module,
                patient_id=self.patient_ids[self.patient.currentIndex()],
                record_date=parse_date(self.record_date.text()),
                profile=self.profile.currentText(),
                inputs=values,
                result=result,
                notes=notes,
            )
            record_id = self.repository.add(record)
            self.audit_repository.log(
                self.current_user_id,
                "registrou_modulo_avancado",
                "registros_clinicos_avancados",
                record_id,
                f"{self.definition.module}: {result}",
            )
        except (ValueError, IndexError) as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return
        self.result.setPlainText(result)
        self.refresh()
        QMessageBox.information(self, self.definition.title, "Registro avancado salvo.")

    def _clear(self) -> None:
        for field in self.inputs.values():
            field.clear()
        self.notes.clear()
        self.result.clear()
        self.record_date.setText(today_text())

    def _load_patients(self) -> None:
        current = self.patient.currentText()
        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids = [None]
        self.patient.addItem("Sem paciente vinculado")
        for patient in self.patient_repository.list_active():
            self.patient_ids.append(patient.id)
            self.patient.addItem(patient.name)
        index = self.patient.findText(current)
        if index >= 0:
            self.patient.setCurrentIndex(index)
        self.patient.blockSignals(False)
