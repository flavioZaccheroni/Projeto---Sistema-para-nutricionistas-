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

from nutri_app.domain.integration import (
    ExternalIntegration,
    IntegrationDirection,
    IntegrationExecution,
    IntegrationStatus,
    IntegrationType,
)
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.integration_repository import IntegrationRepository
from nutri_app.repositories.laboratory_exam_repository import LaboratoryExamRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.integration import IntegrationService
from nutri_app.ui.pages.base import Page


class IntegrationsPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Integracoes",
            "Configuracao, simulacao e importacao de dados externos.",
        )
        self.repository = IntegrationRepository(connection_factory)
        self.exam_repository = LaboratoryExamRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = IntegrationService()
        self.integration_ids_by_index: list[int | None] = []
        self.patient_ids_by_index: list[int] = []

        self.name = QLineEdit()
        self.integration_type = QComboBox()
        self.integration_type.addItems([item.value for item in IntegrationType])
        self.endpoint = QLineEdit()
        self.credential_alias = QLineEdit()
        self.notes = QLineEdit()
        self.integration = QComboBox()
        self.patient = QComboBox()
        self.payload = QTextEdit()
        self.payload.setFixedHeight(120)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Nome", self.name)
        form.addRow("Tipo", self.integration_type)
        form.addRow("Endpoint", self.endpoint)
        form.addRow("Credencial alias", self.credential_alias)
        form.addRow("Observacoes", self.notes)

        save = QPushButton("Salvar integracao")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_integration)
        simulate = QPushButton("Simular sync")
        simulate.clicked.connect(self._simulate_sync)

        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(simulate)
        actions.addStretch()

        import_form = QFormLayout()
        import_form.addRow("Integracao", self.integration)
        import_form.addRow("Paciente", self.patient)
        import_form.addRow("Payload JSON exame", self.payload)
        import_form.addRow("Resultado", self.result)
        import_exam = QPushButton("Importar exame")
        import_exam.clicked.connect(self._import_exam)

        self.integrations_table = QTableWidget(0, 5)
        self.integrations_table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Tipo", "Endpoint", "Ativo"]
        )
        self.executions_table = QTableWidget(0, 6)
        self.executions_table.setHorizontalHeaderLabels(
            ["ID", "Integracao", "Direcao", "Entidade", "Status", "Resultado"]
        )

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)
        wrapper_layout.addRow(import_form)
        wrapper_layout.addRow(import_exam)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.integrations_table)
        self.layout.addWidget(self.executions_table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_selects()
        self._reload_tables()

    def _save_integration(self) -> None:
        integration = ExternalIntegration(
            name=self.name.text().strip(),
            integration_type=IntegrationType(self.integration_type.currentText()),
            endpoint=self.endpoint.text().strip(),
            credential_alias=self.credential_alias.text().strip(),
            notes=self.notes.text().strip(),
        )
        try:
            self.service.validate_integration(integration)
        except ValueError as exc:
            QMessageBox.warning(self, "Integracoes", str(exc))
            return
        integration_id = self.repository.add_integration(integration)
        self.repository.add_execution(
            IntegrationExecution(
                integration_id=integration_id,
                direction=IntegrationDirection.EXPORT,
                entity="configuracao",
                status=IntegrationStatus.CONFIGURED,
                result="Integracao configurada.",
            )
        )
        self.audit_repository.log(
            self.current_user_id,
            "criou_integracao_externa",
            "integracoes_externas",
            integration_id,
            integration.name,
        )
        self._clear_form()
        self.refresh()

    def _simulate_sync(self) -> None:
        integration = self._selected_integration()
        if integration is None:
            QMessageBox.warning(self, "Integracoes", "Selecione uma integracao.")
            return
        result = self.service.simulate_sync(integration, "dados clinicos")
        self.repository.add_execution(
            IntegrationExecution(
                integration_id=integration.id,
                direction=IntegrationDirection.EXPORT,
                entity="dados clinicos",
                status=IntegrationStatus.SUCCESS,
                result=result,
            )
        )
        self.result.setPlainText(result)
        self.refresh()

    def _import_exam(self) -> None:
        integration = self._selected_integration()
        if integration is None or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Integracoes", "Selecione integracao e paciente.")
            return
        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        payload = self.payload.toPlainText().strip()
        try:
            exam = self.service.parse_laboratory_payload(payload, patient_id)
            exam_id = self.exam_repository.add(exam)
        except ValueError as exc:
            self.repository.add_execution(
                IntegrationExecution(
                    integration_id=integration.id,
                    direction=IntegrationDirection.IMPORT,
                    entity="exame laboratorial",
                    status=IntegrationStatus.FAILED,
                    payload=payload,
                    result=str(exc),
                )
            )
            QMessageBox.warning(self, "Integracoes", str(exc))
            self.refresh()
            return
        result = f"Exame importado com ID {exam_id}."
        self.repository.add_execution(
            IntegrationExecution(
                integration_id=integration.id,
                direction=IntegrationDirection.IMPORT,
                entity="exame laboratorial",
                status=IntegrationStatus.SUCCESS,
                payload=payload,
                result=result,
            )
        )
        self.audit_repository.log(
            self.current_user_id,
            "importou_exame_integracao",
            "exames_laboratoriais",
            exam_id,
            integration.name,
        )
        self.result.setPlainText(result)
        self.refresh()

    def _reload_selects(self) -> None:
        self.integration.clear()
        self.integration_ids_by_index = []
        for integration in self.repository.list_integrations():
            self.integration.addItem(integration.name)
            self.integration_ids_by_index.append(integration.id)
        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is not None:
                self.patient.addItem(patient.name)
                self.patient_ids_by_index.append(patient.id)

    def _reload_tables(self) -> None:
        integrations = self.repository.list_integrations()
        self.integrations_table.setRowCount(len(integrations))
        for row, integration in enumerate(integrations):
            self.integrations_table.setItem(row, 0, QTableWidgetItem(str(integration.id or "")))
            self.integrations_table.setItem(row, 1, QTableWidgetItem(integration.name))
            integration_type = integration.integration_type.value
            self.integrations_table.setItem(row, 2, QTableWidgetItem(integration_type))
            self.integrations_table.setItem(row, 3, QTableWidgetItem(integration.endpoint))
            active = "Sim" if integration.active else "Nao"
            self.integrations_table.setItem(row, 4, QTableWidgetItem(active))

        executions = self.repository.list_executions()
        self.executions_table.setRowCount(len(executions))
        for row, execution in enumerate(executions):
            self.executions_table.setItem(row, 0, QTableWidgetItem(str(execution.id or "")))
            self.executions_table.setItem(row, 1, QTableWidgetItem(execution.integration_name))
            self.executions_table.setItem(row, 2, QTableWidgetItem(execution.direction.value))
            self.executions_table.setItem(row, 3, QTableWidgetItem(execution.entity))
            self.executions_table.setItem(row, 4, QTableWidgetItem(execution.status.value))
            self.executions_table.setItem(row, 5, QTableWidgetItem(execution.result))

    def _selected_integration(self) -> ExternalIntegration | None:
        if self.integration.currentIndex() < 0 or not self.integration_ids_by_index:
            return None
        integration_id = self.integration_ids_by_index[self.integration.currentIndex()]
        if integration_id is None:
            return None
        return self.repository.get_integration(integration_id)

    def _clear_form(self) -> None:
        self.name.clear()
        self.endpoint.clear()
        self.credential_alias.clear()
        self.notes.clear()
