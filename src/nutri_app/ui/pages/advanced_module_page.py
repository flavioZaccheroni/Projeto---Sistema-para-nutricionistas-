from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
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
        self.lab_indicator_labels: dict[str, QLabel] = {}
        self.lab_status = QLabel()

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
            if definition.module == "Exames Avancados":
                field.textChanged.connect(self._refresh_advanced_labs_indicators)
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        if definition.module == "Exames Avancados":
            self._build_advanced_labs_layout(actions)
        else:
            wrapper = QWidget()
            wrapper_layout = QFormLayout(wrapper)
            wrapper_layout.addRow(form)
            wrapper_layout.addRow(actions)
            self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def _build_advanced_labs_layout(self, actions: QHBoxLayout) -> None:
        header = QGroupBox("Informacoes do Paciente & Avaliacao")
        header_layout = QGridLayout(header)
        header_layout.addWidget(QLabel("Paciente"), 0, 0)
        header_layout.addWidget(self.patient, 1, 0)
        header_layout.addWidget(QLabel("Perfil"), 0, 1)
        header_layout.addWidget(self.profile, 1, 1)
        header_layout.addWidget(QLabel("Data"), 2, 0)
        header_layout.addWidget(self.record_date, 3, 0)
        self.lab_status = QLabel("Avaliacao Laboratorial\nIniciado")
        self.lab_status.setObjectName("statusPanel")
        header_layout.addWidget(self.lab_status, 0, 2, 4, 1)
        header_layout.setColumnStretch(0, 1)
        header_layout.setColumnStretch(1, 1)
        header_layout.setColumnStretch(2, 1)

        markers = QGroupBox("Marcadores Laboratoriais (Painel de Dados)")
        marker_layout = QGridLayout(markers)
        marker_layout.addWidget(QLabel("Secao 1 (Valores Criticos)"), 0, 0, 1, 3)
        marker_layout.addWidget(QLabel("Secao 2 (Glicemia e Outros)"), 0, 4, 1, 3)
        left_keys = ["albumin", "crp", "potassium", "phosphorus"]
        right_keys = ["hemoglobin", "hba1c"]
        for row, key in enumerate(left_keys):
            self._add_lab_marker(marker_layout, row + 1, 0, key)
        for row, key in enumerate(right_keys):
            self._add_lab_marker(marker_layout, row + 1, 4, key)
        marker_layout.setColumnStretch(1, 1)
        marker_layout.setColumnStretch(5, 1)

        output = QGroupBox("Observacoes & Resultado (Painel de Saida)")
        output_layout = QGridLayout(output)
        output_layout.addWidget(QLabel("Observacoes"), 0, 0)
        output_layout.addWidget(QLabel("Resultado"), 0, 1)
        output_layout.addWidget(self.notes, 1, 0)
        result_card = QGroupBox("Resumo de Resultados e Alertas")
        result_layout = QVBoxLayout(result_card)
        result_layout.addWidget(self.result)
        output_layout.addWidget(result_card, 1, 1)
        output_layout.setColumnStretch(0, 1)
        output_layout.setColumnStretch(1, 1)

        self.layout.addWidget(header)
        self.layout.addWidget(markers)
        self.layout.addWidget(output)
        self.layout.addLayout(actions)
        self._refresh_advanced_labs_indicators()

    def _add_lab_marker(self, layout: QGridLayout, row: int, column: int, key: str) -> None:
        layout.addWidget(QLabel(self._field_label(key)), row, column)
        layout.addWidget(self.inputs[key], row, column + 1)
        indicator = QLabel("Normal")
        indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator.setObjectName("labStateNormal")
        self.lab_indicator_labels[key] = indicator
        layout.addWidget(indicator, row, column + 2)

    def _refresh_advanced_labs_indicators(self, *_args: object) -> None:
        if self.definition.module != "Exames Avancados" or not self.lab_indicator_labels:
            return
        critical_count = 0
        filled_count = 0
        for key, label in self.lab_indicator_labels.items():
            text = self.inputs[key].text().strip()
            status = self._lab_marker_status(key, text)
            if text:
                filled_count += 1
            if status == "Critico":
                critical_count += 1
            label.setText(status)
            label.setObjectName("labStateCritical" if status == "Critico" else "labStateNormal")
            label.style().unpolish(label)
            label.style().polish(label)
        if critical_count:
            self.lab_status.setText(f"Avaliacao Laboratorial\n{critical_count} alerta(s)")
        elif filled_count:
            self.lab_status.setText("Avaliacao Laboratorial\nSem alertas")
        else:
            self.lab_status.setText("Avaliacao Laboratorial\nIniciado")

    def _lab_marker_status(self, key: str, value: str) -> str:
        try:
            parsed = float(value.replace(",", ".")) if value else 0
        except ValueError:
            return "Critico"
        if not value:
            return "Normal"
        critical = {
            "albumin": parsed < 3.5,
            "crp": parsed > 10,
            "potassium": parsed > 5.5,
            "phosphorus": parsed > 4.5,
            "hemoglobin": parsed < 12,
            "hba1c": parsed >= 6.5,
        }
        return "Critico" if critical.get(key, False) else "Normal"

    def _field_label(self, key: str) -> str:
        for field_key, label in self.definition.fields:
            if field_key == key:
                return label
        return key

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
        self._refresh_advanced_labs_indicators()
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
