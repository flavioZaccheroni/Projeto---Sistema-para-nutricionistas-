from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
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

from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.base import Page


class PatientsPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Cadastro de Pacientes", "Dados pessoais, contato e historico clinico.")
        self.repository = PatientRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.selected_patient_id: int | None = None

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar por nome, telefone, e-mail ou documento")
        self.search.textChanged.connect(self._reload_table)

        self.name = QLineEdit()
        self.birth_date = QLineEdit()
        self.birth_date.setPlaceholderText("AAAA-MM-DD")
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.health_insurance = QLineEdit()
        self.document = QLineEdit()
        self.responsible = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Nome completo", self.name)
        form.addRow("Data de nascimento", self.birth_date)
        form.addRow("Telefone", self.phone)
        form.addRow("E-mail", self.email)
        form.addRow("Convenio", self.health_insurance)
        form.addRow("Documento", self.document)
        form.addRow("Responsavel", self.responsible)
        form.addRow("Observacoes clinicas", self.notes)

        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_patient)
        clear = QPushButton("Novo")
        clear.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_patient)

        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(clear)
        actions.addWidget(delete)
        actions.addStretch()

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Nascimento", "Telefone", "E-mail", "Convenio", "Documento"]
        )
        self.table.cellClicked.connect(self._select_patient_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow("Pesquisar", self.search)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self._reload_table()

    def _save_patient(self) -> None:
        try:
            patient = Patient(
                id=self.selected_patient_id,
                name=self.name.text().strip(),
                birth_date=date.fromisoformat(self.birth_date.text().strip()),
                phone=self.phone.text().strip(),
                email=self.email.text().strip(),
                health_insurance=self.health_insurance.text().strip(),
                document=self.document.text().strip(),
                responsible=self.responsible.text().strip(),
                clinical_notes=self.notes.toPlainText().strip(),
            )
        except ValueError:
            QMessageBox.warning(self, "Validacao", "Use a data no formato AAAA-MM-DD.")
            return

        if not patient.name:
            QMessageBox.warning(self, "Validacao", "Nome completo e obrigatorio.")
            return

        if patient.id is None:
            patient_id = self.repository.add(patient)
            self.audit_repository.log(
                user_id=self.current_user_id,
                action="criou_paciente",
                entity="pacientes",
                entity_id=patient_id,
                details=f"Paciente criado: {patient.name}",
            )
        else:
            self.repository.update(patient)
            patient_id = patient.id
            self.audit_repository.log(
                user_id=self.current_user_id,
                action="atualizou_paciente",
                entity="pacientes",
                entity_id=patient_id,
                details=f"Paciente atualizado: {patient.name}",
            )

        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_patient_id = None
        self.name.clear()
        self.birth_date.clear()
        self.phone.clear()
        self.email.clear()
        self.health_insurance.clear()
        self.document.clear()
        self.responsible.clear()
        self.notes.clear()

    def _reload_table(self) -> None:
        patients = self.repository.search(self.search.text())
        self.table.setRowCount(len(patients))
        for row, patient in enumerate(patients):
            self.table.setItem(row, 0, QTableWidgetItem(str(patient.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(patient.name))
            self.table.setItem(row, 2, QTableWidgetItem(patient.birth_date.isoformat()))
            self.table.setItem(row, 3, QTableWidgetItem(patient.phone))
            self.table.setItem(row, 4, QTableWidgetItem(patient.email))
            self.table.setItem(row, 5, QTableWidgetItem(patient.health_insurance))
            self.table.setItem(row, 6, QTableWidgetItem(patient.document))

    def _select_patient_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        patient = self.repository.get(int(item.text()))
        if patient is None:
            QMessageBox.warning(self, "Paciente", "Paciente nao encontrado.")
            self._reload_table()
            return

        self.selected_patient_id = patient.id
        self.name.setText(patient.name)
        self.birth_date.setText(patient.birth_date.isoformat())
        self.phone.setText(patient.phone)
        self.email.setText(patient.email)
        self.health_insurance.setText(patient.health_insurance)
        self.document.setText(patient.document)
        self.responsible.setText(patient.responsible)
        self.notes.setPlainText(patient.clinical_notes)

    def _delete_patient(self) -> None:
        if self.selected_patient_id is None:
            QMessageBox.warning(self, "Paciente", "Selecione um paciente para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir paciente",
            "Deseja excluir este paciente? O historico sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        patient_id = self.selected_patient_id
        self.repository.soft_delete(patient_id)
        self.audit_repository.log(
            user_id=self.current_user_id,
            action="excluiu_paciente",
            entity="pacientes",
            entity_id=patient_id,
            details="Paciente removido por exclusao logica.",
        )
        self._clear_form()
        self._reload_table()
