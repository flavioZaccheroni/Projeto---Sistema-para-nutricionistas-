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

from nutri_app.domain.ai_assistant import AIAssistantExecution, AIAssistantRequestType
from nutri_app.repositories.ai_assistant_repository import AIAssistantRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.ai_assistant import AIAssistantService
from nutri_app.ui.date_format import format_datetime
from nutri_app.ui.pages.base import Page


class AIAssistantPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "IA Assistiva",
            "Sugestoes, substituicoes, resumo e alertas com revisao profissional.",
        )
        self.repository = AIAssistantRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = AIAssistantService()
        self.patient_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar historico por paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.request_type = QComboBox()
        self.request_type.addItems([item.value for item in AIAssistantRequestType])
        self.prompt = QTextEdit()
        self.prompt.setFixedHeight(70)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setFixedHeight(180)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Tipo", self.request_type)
        form.addRow("Contexto adicional", self.prompt)
        form.addRow("Resultado", self.result)

        generate = QPushButton("Gerar assistencia")
        generate.setObjectName("primaryButton")
        generate.clicked.connect(self._generate)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)

        actions = QHBoxLayout()
        actions.addWidget(generate)
        actions.addWidget(refresh)
        actions.addStretch()

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Tipo", "Status", "Alertas", "Criado em"]
        )
        self.table.cellClicked.connect(self._select_execution_from_table)

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

    def _generate(self) -> None:
        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        request_type = AIAssistantRequestType(self.request_type.currentText())
        prompt = self.prompt.toPlainText().strip()
        context = self.repository.build_context(patient_id)
        generated = self.service.generate(request_type, context, prompt)
        execution = AIAssistantExecution(
            patient_id=patient_id,
            request_type=request_type,
            input_text=prompt,
            result=generated.result,
            alerts="\n".join(generated.alerts),
            status=generated.status,
            notes="Gerado por assistente local baseado em regras.",
        )
        execution_id = self.repository.add_execution(execution)
        self.audit_repository.log(
            self.current_user_id,
            "gerou_ia_assistiva",
            "ia_assistente_execucoes",
            execution_id,
            request_type.value,
        )
        self.result.setPlainText(generated.result)
        self._reload_table()
        QMessageBox.information(self, "IA Assistiva", "Resultado assistivo gerado.")

    def _reload_patients(self) -> None:
        current_id = (
            self.patient_ids_by_index[self.patient.currentIndex()]
            if self.patient.currentIndex() >= 0 and self.patient_ids_by_index
            else None
        )
        self.patient.clear()
        self.patient_ids_by_index = [None]
        self.patient.addItem("Sem paciente")
        for patient in self.patient_repository.list_active():
            if patient.id is not None:
                self.patient.addItem(patient.name)
                self.patient_ids_by_index.append(patient.id)
        if current_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_id))

    def _reload_table(self) -> None:
        records = self.repository.list_executions(self.search.text())
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.patient_name))
            self.table.setItem(row, 2, QTableWidgetItem(record.request_type.value))
            self.table.setItem(row, 3, QTableWidgetItem(record.status))
            self.table.setItem(row, 4, QTableWidgetItem(record.alerts))
            created_at = format_datetime(record.created_at)
            self.table.setItem(row, 5, QTableWidgetItem(created_at))

    def _select_execution_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        execution_id = int(item.text())
        for execution in self.repository.list_executions():
            if execution.id == execution_id:
                self.result.setPlainText(execution.result)
                return
