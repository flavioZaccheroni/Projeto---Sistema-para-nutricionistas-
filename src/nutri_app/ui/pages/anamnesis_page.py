from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nutri_app.domain.anamnesis import Anamnesis
from nutri_app.repositories.anamnesis_repository import AnamnesisRepository
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.ui.anamnesis_form import (
    ALERGIAS_INTOLERANCIAS,
    COMPORTAMENTO_ALIMENTAR,
    HABITOS_VIDA,
    HISTORIA_DOENCA_ATUAL,
    HISTORICO_FAMILIAR,
    HISTORICO_PATOLOGICO,
    MEDICAMENTOS_SUPLEMENTOS,
    OBSERVACOES_CLINICAS,
    QUEIXA_PRINCIPAL,
    ROTINA_ALIMENTAR,
    SINTOMAS_GASTROINTESTINAIS,
    SelectableSection,
    load_sections,
    serialize_sections,
    summarize_anamnesis_text,
)
from nutri_app.ui.date_format import format_datetime
from nutri_app.ui.pages.advanced_module_page import AdvancedModulePage
from nutri_app.ui.pages.base import Page


class AnamnesisPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Anamnese", "Queixa principal, historico, rotina alimentar e sintomas.")
        self.repository = AnamnesisRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.advanced_page = AdvancedModulePage(
            AdvancedClinicalService().by_module("Anamnese Avancada"),
            connection_factory,
            audit_repository,
            current_user_id,
        )
        self.selected_anamnesis_id: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()

        self.chief_complaint = SelectableSection(QUEIXA_PRINCIPAL)
        self.current_disease_history = SelectableSection(HISTORIA_DOENCA_ATUAL)
        self.pathological_history = SelectableSection(HISTORICO_PATOLOGICO)
        self.family_history = SelectableSection(HISTORICO_FAMILIAR)
        self.food_routine = SelectableSection(ROTINA_ALIMENTAR)
        self.eating_behavior = SelectableSection(COMPORTAMENTO_ALIMENTAR)
        self.gastrointestinal_symptoms = SelectableSection(SINTOMAS_GASTROINTESTINAIS)
        self.observations_section = SelectableSection(OBSERVACOES_CLINICAS)
        self.habits_sections = [SelectableSection(definition) for definition in HABITOS_VIDA]
        self.medication_sections = [
            SelectableSection(definition)
            for definition in MEDICAMENTOS_SUPLEMENTOS
        ]
        self.allergy_sections = [
            SelectableSection(definition)
            for definition in ALERGIAS_INTOLERANCIAS
        ]

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Consulta vinculada", self.appointment)

        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_anamnesis)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_anamnesis)

        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(new)
        actions.addWidget(delete)
        actions.addStretch()

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Consulta", "Queixa", "Atualizado em"]
        )
        self.table.cellClicked.connect(self._select_anamnesis_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        section_tabs = QTabWidget()
        section_tabs.addTab(
            self._scroll_tab([
                self.chief_complaint,
                self.current_disease_history,
                self.pathological_history,
                self.family_history,
            ]),
            "Clinica",
        )
        section_tabs.addTab(
            self._scroll_tab([
                self.food_routine,
                self.eating_behavior,
                self.gastrointestinal_symptoms,
            ]),
            "Alimentacao e GI",
        )
        section_tabs.addTab(
            self._scroll_tab([self.observations_section, *self.habits_sections]),
            "Habitos e observacoes",
        )
        section_tabs.addTab(
            self._scroll_tab([*self.medication_sections, *self.allergy_sections]),
            "Medicamentos e alergias",
        )

        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.addWidget(wrapper)
        basic_layout.addWidget(section_tabs)
        basic_layout.addWidget(self.table)

        tabs = QTabWidget()
        tabs.addTab(basic_tab, "Basica")
        tabs.addTab(self.advanced_page, "Avancada")

        self.layout.addWidget(tabs)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_table()
        self.advanced_page.refresh()

    def _save_anamnesis(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Anamnese", "Cadastre um paciente antes de criar anamnese.")
            return

        anamnesis = Anamnesis(
            id=self.selected_anamnesis_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            chief_complaint=self.chief_complaint.to_text(),
            current_disease_history=self.current_disease_history.to_text(),
            pathological_history=self.pathological_history.to_text(),
            family_history=self.family_history.to_text(),
            food_routine=self.food_routine.to_text(),
            eating_behavior=self.eating_behavior.to_text(),
            gastrointestinal_symptoms=self.gastrointestinal_symptoms.to_text(),
            notes=self._notes_text(),
        )

        if not self.chief_complaint.has_content():
            QMessageBox.warning(self, "Validacao", "Queixa principal e obrigatoria.")
            return

        if anamnesis.id is None:
            anamnesis_id = self.repository.add(anamnesis)
            self._audit("criou_anamnese", anamnesis_id, "Anamnese criada.")
        else:
            self.repository.update(anamnesis)
            anamnesis_id = anamnesis.id
            self._audit("atualizou_anamnese", anamnesis_id, "Anamnese atualizada.")

        self._clear_form()
        self._reload_table()

    def _delete_anamnesis(self) -> None:
        if self.selected_anamnesis_id is None:
            QMessageBox.warning(self, "Anamnese", "Selecione uma anamnese para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir anamnese",
            "Deseja excluir esta anamnese? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        anamnesis_id = self.selected_anamnesis_id
        self.repository.soft_delete(anamnesis_id)
        self._audit("excluiu_anamnese", anamnesis_id, "Anamnese removida por exclusao logica.")
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_anamnesis_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        for section in self._section_widgets():
            section.clear()

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
            self.table.setItem(row, 3, QTableWidgetItem(
                summarize_anamnesis_text(record.chief_complaint)
            ))
            self.table.setItem(row, 4, QTableWidgetItem(format_datetime(record.updated_at)))

    def _select_anamnesis_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Anamnese", "Registro nao encontrado.")
            self._reload_table()
            return

        self.selected_anamnesis_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.chief_complaint.set_text(record.chief_complaint)
        self.current_disease_history.set_text(record.current_disease_history)
        self.pathological_history.set_text(record.pathological_history)
        self.family_history.set_text(record.family_history)
        self.food_routine.set_text(record.food_routine)
        self.eating_behavior.set_text(record.eating_behavior)
        self.gastrointestinal_symptoms.set_text(record.gastrointestinal_symptoms)
        self._load_notes(record.notes)

    def _section_widgets(self) -> list[SelectableSection]:
        return [
            self.chief_complaint,
            self.current_disease_history,
            self.pathological_history,
            self.family_history,
            self.food_routine,
            self.eating_behavior,
            self.gastrointestinal_symptoms,
            self.observations_section,
            *self.habits_sections,
            *self.medication_sections,
            *self.allergy_sections,
        ]

    def _notes_text(self) -> str:
        return serialize_sections([
            self.observations_section,
            *self.habits_sections,
            *self.medication_sections,
            *self.allergy_sections,
        ])

    def _load_notes(self, text: str) -> None:
        load_sections([
            self.observations_section,
            *self.habits_sections,
            *self.medication_sections,
            *self.allergy_sections,
        ], text)

    def _scroll_tab(self, sections: list[SelectableSection]) -> QScrollArea:
        content = QWidget()
        layout = QVBoxLayout(content)
        for section in sections:
            layout.addWidget(section)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _audit(self, action: str, anamnesis_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="anamnese",
            entity_id=anamnesis_id,
            details=details,
        )
