from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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

from nutri_app.domain.physical_exam import NutritionPhysicalExam
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.physical_exam_repository import PhysicalExamRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.date_format import format_date, parse_date, today_text
from nutri_app.ui.input_masks import apply_date_mask
from nutri_app.ui.pages.base import Page


class PhysicalExamPage(Page):
    FINDINGS = [
        ("estado_geral", "Estado geral"),
        ("consciencia", "Consciencia"),
        ("desempenho_funcional", "Desempenho funcional"),
        ("mobilidade", "Mobilidade"),
        ("hidratacao", "Hidratacao"),
        ("edema", "Edema"),
        ("ascite", "Ascite"),
        ("musculo_temporal", "Musculo temporal"),
        ("musculo_clavicular", "Musculo clavicular"),
        ("musculo_ombro", "Musculo do ombro"),
        ("musculo_interosseo", "Musculo interosseo"),
        ("musculo_coxa", "Musculo da coxa"),
        ("musculo_panturrilha", "Musculo da panturrilha"),
        ("gordura_orbital", "Gordura orbital"),
        ("gordura_tricipital", "Gordura tricipital"),
        ("gordura_costal", "Gordura costal"),
        ("pele", "Pele"),
        ("cabelos", "Cabelos"),
        ("unhas", "Unhas"),
        ("cavidade_oral", "Cavidade oral"),
        ("denticao", "Denticao"),
        ("degluticao", "Degluticao"),
        ("feridas", "Feridas"),
        ("lesao_pressao", "Lesao por pressao"),
    ]
    STATES = [
        "Nao avaliado",
        "Ausente",
        "Preservado",
        "Leve",
        "Moderado",
        "Grave",
        "Alterado",
        "Nao aplicavel",
    ]

    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Avaliacao Clinica",
            "Exame fisico nutricional estruturado e comparacao longitudinal.",
        )
        self.repository = PhysicalExamRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id

        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_history)
        self.patient_ids: list[int | None] = []
        self.assessment_date = QLineEdit(today_text())
        apply_date_mask(self.assessment_date)
        self.diagnosis_id = QLineEdit()
        self.diagnosis_id.setPlaceholderText("Opcional")
        self.severity = QComboBox()
        self.severity.addItems(["Sem alerta", "Leve", "Moderada", "Grave", "Critica"])

        header = QGroupBox("Identificacao da avaliacao")
        header_layout = QGridLayout(header)
        self._field(header_layout, 0, 0, "Paciente", self.patient)
        self._field(header_layout, 0, 1, "Data", self.assessment_date)
        self._field(header_layout, 0, 2, "Diagnostico vinculado (ID)", self.diagnosis_id)
        self._field(header_layout, 0, 3, "Gravidade global", self.severity)
        for column in range(4):
            header_layout.setColumnStretch(column, 1)

        findings_box = QGroupBox("Achados estruturados")
        findings_layout = QGridLayout(findings_box)
        self.findings: dict[str, QComboBox] = {}
        for index, (key, label) in enumerate(self.FINDINGS):
            column_group = index % 4
            row_group = (index // 4) * 2
            combo = QComboBox()
            combo.addItems(self.STATES)
            self.findings[key] = combo
            self._field(findings_layout, row_group, column_group, label, combo)
            findings_layout.setColumnStretch(column_group, 1)

        details = QGroupBox("Sinais, resumo e imagem clinica")
        details_layout = QGridLayout(details)
        self.signs_symptoms = QTextEdit()
        self.signs_symptoms.setFixedHeight(65)
        self.summary = QTextEdit()
        self.summary.setFixedHeight(65)
        self.image_path = QLineEdit()
        choose_image = QPushButton("Selecionar imagem")
        choose_image.clicked.connect(self._choose_image)
        self.image_consent = QCheckBox("Consentimento especifico para imagem registrado")
        details_layout.addWidget(QLabel("Sinais e sintomas"), 0, 0)
        details_layout.addWidget(QLabel("Resumo dos achados"), 0, 1)
        details_layout.addWidget(self.signs_symptoms, 1, 0)
        details_layout.addWidget(self.summary, 1, 1)
        details_layout.addWidget(QLabel("Imagem autorizada"), 2, 0)
        image_row = QHBoxLayout()
        image_row.addWidget(self.image_path)
        image_row.addWidget(choose_image)
        details_layout.addLayout(image_row, 3, 0, 1, 2)
        details_layout.addWidget(self.image_consent, 4, 0, 1, 2)
        details_layout.setColumnStretch(0, 1)
        details_layout.setColumnStretch(1, 1)

        save = QPushButton("Salvar avaliacao")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self._clear)
        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(clear)
        actions.addStretch()

        self.comparison = QLabel("Selecione um paciente para consultar a evolucao.")
        self.comparison.setWordWrap(True)
        self.comparison.setObjectName("statusPanel")
        self.history = QTableWidget(0, 5)
        self.history.setHorizontalHeaderLabels(["ID", "Data", "Gravidade", "Resumo", "Imagem"])
        self.history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history.verticalHeader().setVisible(False)
        self.history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.layout.addWidget(header)
        self.layout.addWidget(findings_box)
        self.layout.addWidget(details)
        self.layout.addLayout(actions)
        self.layout.addWidget(self.comparison)
        self.layout.addWidget(self.history)
        self._load_patients()

    def _field(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        label: str,
        widget: QWidget,
    ) -> None:
        caption = QLabel(label)
        caption.setObjectName("miniHeader")
        layout.addWidget(caption, row, column)
        layout.addWidget(widget, row + 1, column)

    def _load_patients(self) -> None:
        self.patient.clear()
        self.patient_ids = [None]
        self.patient.addItem("Selecione um paciente")
        for patient in self.patient_repository.list_active():
            self.patient_ids.append(patient.id)
            self.patient.addItem(f"{patient.medical_record_number} - {patient.name}")

    def _save(self) -> None:
        patient_id = self.patient_ids[self.patient.currentIndex()]
        if patient_id is None:
            QMessageBox.warning(self, "Avaliacao clinica", "Selecione um paciente.")
            return
        diagnosis_text = self.diagnosis_id.text().strip()
        try:
            exam = NutritionPhysicalExam(
                patient_id=patient_id,
                diagnosis_id=int(diagnosis_text) if diagnosis_text else None,
                assessment_date=parse_date(self.assessment_date.text()),
                findings={key: field.currentText() for key, field in self.findings.items()},
                signs_symptoms=self.signs_symptoms.toPlainText(),
                summary=self.summary.toPlainText(),
                severity=self.severity.currentText(),
                image_path=self.image_path.text(),
                image_consent=self.image_consent.isChecked(),
            )
            exam_id = self.repository.add(exam)
            comparison = self.repository.compare_to_previous(exam_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Avaliacao clinica", str(exc))
            return
        self.audit_repository.log(
            self.current_user_id,
            "registrou_exame_fisico_nutricional",
            "exames_fisicos_nutricionais",
            exam_id,
            f"Paciente {patient_id}; gravidade {exam.severity}.",
        )
        self.comparison.setText("Comparacao com avaliacao anterior: " + "; ".join(comparison))
        self._reload_history()
        QMessageBox.information(self, "Avaliacao clinica", "Exame fisico registrado.")

    def _reload_history(self, *_args: object) -> None:
        if not self.patient_ids or self.patient.currentIndex() >= len(self.patient_ids):
            return
        patient_id = self.patient_ids[self.patient.currentIndex()]
        records = self.repository.list_for_patient(patient_id) if patient_id else []
        self.history.setRowCount(len(records))
        for row, exam in enumerate(records):
            values = [
                str(exam.id or ""),
                format_date(exam.assessment_date),
                exam.severity,
                exam.summary,
                "Sim" if exam.image_path else "Nao",
            ]
            for column, value in enumerate(values):
                self.history.setItem(row, column, QTableWidgetItem(value))

    def _choose_image(self) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem clinica autorizada",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp)",
        )
        if path:
            self.image_path.setText(path)

    def _clear(self) -> None:
        self.assessment_date.setText(today_text())
        self.diagnosis_id.clear()
        self.severity.setCurrentText("Sem alerta")
        for field in self.findings.values():
            field.setCurrentText("Nao avaliado")
        self.signs_symptoms.clear()
        self.summary.clear()
        self.image_path.clear()
        self.image_consent.setChecked(False)
