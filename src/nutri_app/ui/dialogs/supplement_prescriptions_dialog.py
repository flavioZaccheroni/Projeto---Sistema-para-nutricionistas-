from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from nutri_app.domain.supplement_prescription import SupplementFollowUp, SupplementPrescription
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.supplement_prescription_repository import (
    SupplementPrescriptionRepository,
)
from nutri_app.repositories.supplement_repository import SupplementRepository
from nutri_app.ui.date_format import format_date, parse_date, today_text
from nutri_app.ui.input_masks import apply_date_mask


class SupplementPrescriptionsDialog(QDialog):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
        initial_supplement_id: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.repository = SupplementPrescriptionRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.supplement_repository = SupplementRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.selected_prescription_id: int | None = None
        self.patient_ids: list[int | None] = []
        self.supplement_ids: list[int | None] = []

        self.setWindowTitle("Prescricoes de suplementacao")
        self.resize(1100, 760)

        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_prescriptions)
        self.supplement = QComboBox()
        self.start_date = QLineEdit(today_text())
        self.end_date = QLineEdit(today_text())
        apply_date_mask(self.start_date)
        apply_date_mask(self.end_date)
        self.quantity = QLineEdit()
        self.unit = QLineEdit("g")
        self.frequency = QSpinBox()
        self.frequency.setRange(1, 24)
        self.times = QLineEdit()
        self.times.setPlaceholderText("Ex.: 08:00, 16:00")
        self.objective = QLineEdit()
        self.instructions = QTextEdit()
        self.instructions.setFixedHeight(55)

        prescription_form = QGridLayout()
        fields = [
            ("Paciente", self.patient),
            ("Produto", self.supplement),
            ("Inicio", self.start_date),
            ("Fim", self.end_date),
            ("Quantidade por dose", self.quantity),
            ("Unidade", self.unit),
            ("Frequencia/dia", self.frequency),
            ("Horarios", self.times),
            ("Objetivo", self.objective),
        ]
        for index, (label, widget) in enumerate(fields):
            row, column = divmod(index, 3)
            form = QFormLayout()
            form.addRow(label, widget)
            prescription_form.addLayout(form, row, column)
        prescription_form.addWidget(QLabel("Instrucoes"), 3, 0)
        prescription_form.addWidget(self.instructions, 4, 0, 1, 3)

        prescribe = QPushButton("Criar prescricao")
        prescribe.setObjectName("primaryButton")
        prescribe.clicked.connect(self._prescribe)
        close = QPushButton("Fechar")
        close.clicked.connect(self.accept)
        actions = QHBoxLayout()
        actions.addWidget(prescribe)
        actions.addStretch()
        actions.addWidget(close)

        self.prescriptions = QTableWidget(0, 8)
        self.prescriptions.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fim", "Produto", "Dose", "Frequencia", "Status", "Aporte/dia"]
        )
        self.prescriptions.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prescriptions.verticalHeader().setVisible(False)
        self.prescriptions.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.prescriptions.cellClicked.connect(self._select_prescription)

        self.follow_up_date = QLineEdit(today_text())
        apply_date_mask(self.follow_up_date)
        self.acceptance = QSpinBox()
        self.acceptance.setRange(0, 10)
        self.adherence = QSpinBox()
        self.adherence.setRange(0, 100)
        self.adherence.setSuffix("%")
        self.incidents = QLineEdit()
        self.clinical_response = QLineEdit()
        self.suspension_reason = QLineEdit()
        follow_form = QGridLayout()
        follow_fields = [
            ("Data", self.follow_up_date),
            ("Aceitacao 0-10", self.acceptance),
            ("Adesao", self.adherence),
            ("Intercorrencias", self.incidents),
            ("Resposta clinica", self.clinical_response),
            ("Motivo de suspensao", self.suspension_reason),
        ]
        for index, (label, widget) in enumerate(follow_fields):
            row, column = divmod(index, 3)
            form = QFormLayout()
            form.addRow(label, widget)
            follow_form.addLayout(form, row, column)
        save_follow_up = QPushButton("Registrar acompanhamento")
        save_follow_up.clicked.connect(self._save_follow_up)

        self.follow_ups = QTableWidget(0, 6)
        self.follow_ups.setHorizontalHeaderLabels(
            ["Data", "Aceitacao", "Adesao", "Intercorrencias", "Resposta", "Suspensao"]
        )
        self.follow_ups.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.follow_ups.verticalHeader().setVisible(False)
        self.follow_ups.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nova prescricao individualizada"))
        layout.addLayout(prescription_form)
        layout.addLayout(actions)
        layout.addWidget(self.prescriptions)
        layout.addWidget(QLabel("Acompanhamento da prescricao selecionada"))
        layout.addLayout(follow_form)
        layout.addWidget(save_follow_up)
        layout.addWidget(self.follow_ups)
        self._load_options(initial_supplement_id)

    def _load_options(self, initial_supplement_id: int | None) -> None:
        self.patient_ids = [None]
        self.patient.addItem("Selecione")
        for patient in self.patient_repository.list_active():
            self.patient_ids.append(patient.id)
            self.patient.addItem(f"{patient.medical_record_number} - {patient.name}")
        self.supplement_ids = [None]
        self.supplement.addItem("Selecione")
        for supplement in self.supplement_repository.list_active():
            self.supplement_ids.append(supplement.id)
            self.supplement.addItem(supplement.name)
        if initial_supplement_id in self.supplement_ids:
            self.supplement.setCurrentIndex(self.supplement_ids.index(initial_supplement_id))

    def _prescribe(self) -> None:
        patient_id = self.patient_ids[self.patient.currentIndex()]
        supplement_id = self.supplement_ids[self.supplement.currentIndex()]
        if patient_id is None or supplement_id is None:
            QMessageBox.warning(self, "Suplementacao", "Selecione paciente e produto.")
            return
        try:
            prescription = SupplementPrescription(
                patient_id=patient_id,
                supplement_id=supplement_id,
                start_date=parse_date(self.start_date.text()),
                end_date=parse_date(self.end_date.text()),
                quantity=float(self.quantity.text().replace(",", ".")),
                unit=self.unit.text(),
                frequency_per_day=self.frequency.value(),
                times=self.times.text(),
                objective=self.objective.text(),
                instructions=self.instructions.toPlainText(),
            )
            prescription_id = self.repository.add(prescription)
        except ValueError as exc:
            QMessageBox.warning(self, "Suplementacao", str(exc))
            return
        self.audit_repository.log(
            self.current_user_id,
            "prescreveu_suplemento",
            "prescricoes_suplementos",
            prescription_id,
            f"Paciente {patient_id}; suplemento {supplement_id}.",
        )
        self._reload_prescriptions()
        QMessageBox.information(self, "Suplementacao", "Prescricao registrada.")

    def _reload_prescriptions(self, *_args: object) -> None:
        if not self.patient_ids or self.patient.currentIndex() >= len(self.patient_ids):
            return
        patient_id = self.patient_ids[self.patient.currentIndex()]
        records = self.repository.list_for_patient(patient_id) if patient_id else []
        self.prescriptions.setRowCount(len(records))
        for row, record in enumerate(records):
            intake = record.daily_intake or {}
            values = [
                str(record.id or ""),
                format_date(record.start_date),
                format_date(record.end_date),
                record.supplement_name,
                f"{record.quantity:g} {record.unit}",
                f"{record.frequency_per_day}x/dia",
                record.status,
                f"{intake.get('energia_kcal', 0):.0f} kcal | P {intake.get('proteina_g', 0):.1f} g",
            ]
            for column, value in enumerate(values):
                self.prescriptions.setItem(row, column, QTableWidgetItem(value))

    def _select_prescription(self, row: int, _column: int) -> None:
        item = self.prescriptions.item(row, 0)
        self.selected_prescription_id = int(item.text()) if item else None
        self._reload_follow_ups()

    def _save_follow_up(self) -> None:
        if self.selected_prescription_id is None:
            QMessageBox.warning(self, "Suplementacao", "Selecione uma prescricao.")
            return
        try:
            follow_up = SupplementFollowUp(
                prescription_id=self.selected_prescription_id,
                record_date=parse_date(self.follow_up_date.text()),
                acceptance=self.acceptance.value(),
                adherence_percent=self.adherence.value(),
                incidents=self.incidents.text(),
                clinical_response=self.clinical_response.text(),
                suspension_reason=self.suspension_reason.text(),
            )
            follow_up_id = self.repository.add_follow_up(follow_up)
        except ValueError as exc:
            QMessageBox.warning(self, "Suplementacao", str(exc))
            return
        self.audit_repository.log(
            self.current_user_id,
            "acompanhou_suplementacao",
            "acompanhamentos_suplementacao",
            follow_up_id,
            f"Prescricao {self.selected_prescription_id}; adesao {follow_up.adherence_percent}%.",
        )
        self._reload_follow_ups()
        self._reload_prescriptions()

    def _reload_follow_ups(self) -> None:
        records = (
            self.repository.list_follow_ups(self.selected_prescription_id)
            if self.selected_prescription_id
            else []
        )
        self.follow_ups.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                format_date(record.record_date),
                str(record.acceptance),
                f"{record.adherence_percent:g}%",
                record.incidents or "-",
                record.clinical_response or "-",
                record.suspension_reason or "-",
            ]
            for column, value in enumerate(values):
                self.follow_ups.setItem(row, column, QTableWidgetItem(value))
