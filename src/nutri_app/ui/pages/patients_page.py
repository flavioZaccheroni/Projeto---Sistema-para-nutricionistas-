from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
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

from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.date_format import DATE_FORMAT, format_date
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
        self.birth_date.setPlaceholderText("mm-dd-aaaa")
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.health_insurance = QLineEdit()
        self.document = QLineEdit()
        self.responsible = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)
        self._configure_field_formats()

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
        self.table.setObjectName("patientCardsTable")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.cellClicked.connect(self._select_patient_from_table)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(12)
        wrapper_layout.addWidget(self._search_card())
        wrapper_layout.addWidget(self._personal_data_cards())
        wrapper_layout.addWidget(self._notes_card())
        wrapper_layout.addLayout(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self._reload_table()

    def _search_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        self._add_inline_field(layout, 0, "Pesquisar", self.search)
        return card

    def _personal_data_cards(self) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.addWidget(self._identity_card(), 0, 0)
        layout.addWidget(self._contact_card(), 0, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return container

    def _identity_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Nome completo", self.name, column_span=2)
        self._add_stacked_field(layout, 2, "Telefone", self.phone, column_span=2)
        self._add_stacked_field(layout, 4, "Convenio", self.health_insurance)
        self._add_stacked_field(layout, 4, "Documento", self.document, column=1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return card

    def _contact_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Data de nascimento", self.birth_date)
        self._add_stacked_field(layout, 2, "E-mail", self.email)
        self._add_stacked_field(layout, 4, "Responsavel", self.responsible)
        return card

    def _notes_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Observacoes clinicas", self.notes)
        return card

    def _add_inline_field(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        widget: QWidget,
    ) -> None:
        title = QLabel(label)
        title.setObjectName("miniHeader")
        layout.addWidget(title, row, 0)
        layout.addWidget(widget, row, 1)
        layout.setColumnStretch(1, 1)

    def _add_stacked_field(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        widget: QWidget,
        column: int = 0,
        column_span: int = 1,
    ) -> None:
        title = QLabel(label)
        title.setObjectName("miniHeader")
        layout.addWidget(title, row, column, 1, column_span)
        layout.addWidget(widget, row + 1, column, 1, column_span)

    def _configure_field_formats(self) -> None:
        self.name.setMaxLength(120)
        self.name.setPlaceholderText("Nome completo")
        self.birth_date.setInputMask("00-00-0000;_")
        self.birth_date.setPlaceholderText("mm-dd-aaaa")
        self.phone.setInputMask("(00) 00000-0000;_")
        self.phone.setPlaceholderText("(00) 00000-0000")
        self.email.setPlaceholderText("nome@email.com")
        self.email.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"^$|^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"),
                self.email,
            )
        )
        self.health_insurance.setMaxLength(80)
        self.health_insurance.setPlaceholderText("Convenio")
        self.document.setInputMask("000.000.000-00;_")
        self.document.setPlaceholderText("CPF")
        self.responsible.setMaxLength(120)
        self.responsible.setPlaceholderText("Responsavel")

    def _save_patient(self) -> None:
        try:
            birth_date = self._required_mask_text(
                self.birth_date,
                "Data de nascimento",
                expected_digits=8,
                expected_format="mm-dd-aaaa",
            )
            phone = self._optional_mask_text(self.phone, "Telefone", expected_digits=11)
            document = self._optional_mask_text(self.document, "Documento", expected_digits=11)
            email = self.email.text().strip()
            if email and not self.email.hasAcceptableInput():
                raise ValueError("E-mail deve estar no formato nome@email.com.")
            patient = Patient(
                id=self.selected_patient_id,
                name=self.name.text().strip(),
                birth_date=self._parse_birth_date(birth_date),
                phone=phone,
                email=email,
                health_insurance=self.health_insurance.text().strip(),
                document=document,
                responsible=self.responsible.text().strip(),
                clinical_notes=self.notes.toPlainText().strip(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Revise os campos informados.")
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

    def _required_mask_text(
        self,
        field: QLineEdit,
        label: str,
        expected_digits: int,
        expected_format: str,
    ) -> str:
        text = field.text().strip()
        digits = "".join(char for char in text if char.isdigit())
        if len(digits) != expected_digits:
            raise ValueError(f"{label} deve estar completo no formato {expected_format}.")
        return text

    def _parse_birth_date(self, value: str) -> date:
        for date_format in [DATE_FORMAT, "%d-%m-%Y"]:
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        raise ValueError("Data de nascimento invalida. Use mm-dd-aaaa ou dd-mm-aaaa.")

    def _optional_mask_text(self, field: QLineEdit, label: str, expected_digits: int) -> str:
        text = field.text().strip()
        digits = "".join(char for char in text if char.isdigit())
        if not digits:
            return ""
        if len(digits) != expected_digits:
            raise ValueError(f"{label} esta incompleto.")
        return text

    def _reload_table(self) -> None:
        patients = self.repository.search(self.search.text())
        self.table.setRowCount(len(patients))
        for row, patient in enumerate(patients):
            self.table.setRowHeight(row, 58)
            values = [
                str(patient.id or ""),
                patient.name,
                format_date(patient.birth_date),
                patient.phone or "-",
                patient.email or "-",
                patient.health_insurance or "-",
                patient.document or "-",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                    | (
                        Qt.AlignmentFlag.AlignCenter
                        if column == 0
                        else Qt.AlignmentFlag.AlignLeft
                    )
                )
                self.table.setItem(row, column, item)

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
        self.birth_date.setText(format_date(patient.birth_date))
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
