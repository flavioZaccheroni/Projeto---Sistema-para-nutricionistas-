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
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.base import Page


class PatientsPage(Page):
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        super().__init__("Cadastro de Pacientes", "Dados pessoais, contato e historico clinico.")
        self.repository = PatientRepository(connection_factory)

        self.name = QLineEdit()
        self.birth_date = QLineEdit()
        self.birth_date.setPlaceholderText("AAAA-MM-DD")
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Nome completo", self.name)
        form.addRow("Data de nascimento", self.birth_date)
        form.addRow("Telefone", self.phone)
        form.addRow("E-mail", self.email)
        form.addRow("Observacoes clinicas", self.notes)

        save = QPushButton("Salvar")
        save.clicked.connect(self._save_patient)
        clear = QPushButton("Novo")
        clear.clicked.connect(self._clear_form)

        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(clear)
        actions.addStretch()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Nascimento", "Telefone"])

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self._reload_table()

    def _save_patient(self) -> None:
        try:
            patient = Patient(
                name=self.name.text().strip(),
                birth_date=date.fromisoformat(self.birth_date.text().strip()),
                phone=self.phone.text().strip(),
                email=self.email.text().strip(),
                clinical_notes=self.notes.toPlainText().strip(),
            )
        except ValueError:
            QMessageBox.warning(self, "Validacao", "Use a data no formato AAAA-MM-DD.")
            return

        if not patient.name:
            QMessageBox.warning(self, "Validacao", "Nome completo e obrigatorio.")
            return

        self.repository.add(patient)
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.name.clear()
        self.birth_date.clear()
        self.phone.clear()
        self.email.clear()
        self.notes.clear()

    def _reload_table(self) -> None:
        patients = self.repository.list_active()
        self.table.setRowCount(len(patients))
        for row, patient in enumerate(patients):
            self.table.setItem(row, 0, QTableWidgetItem(str(patient.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(patient.name))
            self.table.setItem(row, 2, QTableWidgetItem(patient.birth_date.isoformat()))
            self.table.setItem(row, 3, QTableWidgetItem(patient.phone))
