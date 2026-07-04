from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
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

from nutri_app.domain.report import ClinicalReport
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.report_repository import ClinicalReportRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.report import ClinicalReportOptions, ClinicalReportService
from nutri_app.ui.pages.base import Page


class ReportsPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Relatorios",
            "Geracao de relatorio clinico simples e historico de arquivos.",
        )
        self.patient_repository = PatientRepository(connection_factory)
        self.repository = ClinicalReportRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = ClinicalReportService()
        self.patient_ids_by_index: list[int] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar relatorios pelo paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.include_anamnesis = QCheckBox("Anamnese")
        self.include_anthropometry = QCheckBox("Antropometria")
        self.include_laboratory_exams = QCheckBox("Exames")
        self.include_diagnosis = QCheckBox("Diagnostico")
        self.include_meal_plan = QCheckBox("Plano alimentar")
        self.include_energy_expenditure = QCheckBox("Gasto energetico")
        for checkbox in self._section_checkboxes():
            checkbox.setChecked(True)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(220)

        form = QFormLayout()
        form.addRow("Pesquisar historico", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Secoes", self._sections_widget())
        form.addRow("Observacoes", self.notes)
        form.addRow("Pre-visualizacao", self.preview)

        generate = QPushButton("Gerar relatorio")
        generate.setObjectName("primaryButton")
        generate.clicked.connect(self._generate_report)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self._clear_form)

        actions = QHBoxLayout()
        actions.addWidget(generate)
        actions.addWidget(clear)
        actions.addStretch()

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Tipo", "Titulo", "Status", "Arquivo"]
        )
        self.table.cellClicked.connect(self._select_report_from_table)

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

    def _generate_report(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Relatorios", "Cadastre um paciente antes do relatorio.")
            return

        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        patient = self.patient_repository.get(patient_id)
        if patient is None:
            QMessageBox.warning(self, "Relatorios", "Paciente nao encontrado.")
            self.refresh()
            return

        try:
            options = self._build_options()
            context = self.repository.build_clinical_context(patient_id)
            generated = self.service.build(patient, options, context)
            export_dir = Path(__file__).resolve().parents[4] / "exports" / "relatorios"
            file_path = self.service.export_text(generated, export_dir, patient.name)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Dados invalidos.")
            return

        report = ClinicalReport(
            patient_id=patient.id,
            patient_name=patient.name,
            report_type="Clinico simples",
            title=generated.title,
            file_path=str(file_path),
            parameters=generated.parameters,
            content=generated.content,
        )
        report_id = self.repository.add(report)
        self.preview.setPlainText(generated.content)
        self._audit("gerou_relatorio_clinico", report_id, str(file_path))
        self._reload_table()
        QMessageBox.information(self, "Relatorios", f"Relatorio gerado em:\n{file_path}")

    def _build_options(self) -> ClinicalReportOptions:
        return ClinicalReportOptions(
            include_anamnesis=self.include_anamnesis.isChecked(),
            include_anthropometry=self.include_anthropometry.isChecked(),
            include_laboratory_exams=self.include_laboratory_exams.isChecked(),
            include_diagnosis=self.include_diagnosis.isChecked(),
            include_meal_plan=self.include_meal_plan.isChecked(),
            include_energy_expenditure=self.include_energy_expenditure.isChecked(),
            notes=self.notes.toPlainText().strip(),
        )

    def _clear_form(self) -> None:
        self.notes.clear()
        self.preview.clear()
        for checkbox in self._section_checkboxes():
            checkbox.setChecked(True)

    def _reload_patients(self) -> None:
        current_id = (
            self.patient_ids_by_index[self.patient.currentIndex()]
            if self.patient.currentIndex() >= 0 and self.patient_ids_by_index
            else None
        )
        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is not None:
                self.patient.addItem(patient.name)
                self.patient_ids_by_index.append(patient.id)
        if current_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_id))
        self.patient.blockSignals(False)

    def _reload_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.patient_name))
            self.table.setItem(row, 2, QTableWidgetItem(record.report_type))
            self.table.setItem(row, 3, QTableWidgetItem(record.title))
            self.table.setItem(row, 4, QTableWidgetItem(record.status))
            self.table.setItem(row, 5, QTableWidgetItem(record.file_path))

    def _select_report_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        report = self.repository.get(int(item.text()))
        if report is None:
            QMessageBox.warning(self, "Relatorios", "Relatorio nao encontrado.")
            self._reload_table()
            return
        self.preview.setPlainText(report.content)

    def _sections_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        for checkbox in self._section_checkboxes():
            layout.addWidget(checkbox)
        layout.addStretch()
        return widget

    def _section_checkboxes(self) -> list[QCheckBox]:
        return [
            self.include_anamnesis,
            self.include_anthropometry,
            self.include_laboratory_exams,
            self.include_diagnosis,
            self.include_meal_plan,
            self.include_energy_expenditure,
        ]

    def _audit(self, action: str, entity_id: int | None, details: str) -> None:
        self.audit_repository.log(self.current_user_id, action, "relatorios", entity_id, details)
