from __future__ import annotations

from pathlib import Path

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

from nutri_app import __version__
from nutri_app.app.settings import AppSettings
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.release_repository import ReleaseRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.release import ReleaseService
from nutri_app.ui.pages.base import Page


class DeploymentPage(Page):
    def __init__(
        self,
        settings: AppSettings,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Implantacao",
            "Testes finais, checklist de release e preparacao da versao comercial.",
        )
        project_root = Path(__file__).resolve().parents[4]
        self.settings = settings
        self.repository = ReleaseRepository(connection_factory, project_root)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = ReleaseService()

        self.version = QLineEdit(__version__)
        self.version.setReadOnly(True)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Versao", self.version)
        form.addRow("Resumo", self.summary)

        run_checks = QPushButton("Executar checklist")
        run_checks.setObjectName("primaryButton")
        run_checks.clicked.connect(self._run_checks)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)

        actions = QHBoxLayout()
        actions.addWidget(run_checks)
        actions.addWidget(refresh)
        actions.addStretch()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Check", "Status", "Detalhes"])

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        checks = self.repository.list_checks()
        self.table.setRowCount(len(checks))
        for row, check in enumerate(checks):
            self.table.setItem(row, 0, QTableWidgetItem(str(check.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(check.name))
            self.table.setItem(row, 2, QTableWidgetItem(check.status.value))
            self.table.setItem(row, 3, QTableWidgetItem(check.details))

    def _run_checks(self) -> None:
        metrics = self.repository.collect_metrics()
        readiness = self.service.evaluate(metrics, self.version.text())
        self.repository.replace_checks(readiness.checks)
        summary = self.service.release_summary(readiness)
        self.summary.setPlainText(summary)
        self.audit_repository.log(
            self.current_user_id,
            "executou_checklist_implantacao",
            "implantacao_checks",
            None,
            summary,
        )
        self.refresh()
        QMessageBox.information(self, "Implantacao", summary)
