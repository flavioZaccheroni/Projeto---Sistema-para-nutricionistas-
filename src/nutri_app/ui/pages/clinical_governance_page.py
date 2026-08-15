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

from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.clinical_governance_repository import (
    ClinicalGovernanceRepository,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.base import Page


class ClinicalGovernancePage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Governanca Clinica",
            "Fontes, versoes e aprovacao profissional das regras clinicas.",
        )
        self.repository = ClinicalGovernanceRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.selected_reference_id: int | None = None
        self.status = QComboBox()
        self.status.addItems(["Pendente", "Aprovada", "Reprovada"])
        self.reviewer = QLineEdit()
        self.reviewer.setPlaceholderText("Nome completo e CRN/UF")
        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)
        form = QFormLayout()
        form.addRow("Status", self.status)
        form.addRow("Revisor", self.reviewer)
        form.addRow("Parecer/observacoes", self.notes)
        save = QPushButton("Registrar revisao")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)
        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(refresh)
        actions.addStretch()
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Modulo", "Regra", "Versao", "Fonte/limite", "Status", "Revisor", "Revisado em"]
        )
        self.table.cellClicked.connect(self._select)
        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)
        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        records = self.repository.list_references()
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record["id"], record["modulo"], record["regra"], record["versao"],
                record["fonte"], record["status_validacao"], record["revisado_por"] or "",
                record["revisado_em"] or "",
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def _select(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        self.selected_reference_id = int(item.text())
        self.status.setCurrentText(self.table.item(row, 5).text())
        self.reviewer.setText(self.table.item(row, 6).text())

    def _save(self) -> None:
        if self.selected_reference_id is None:
            QMessageBox.warning(self, "Governanca", "Selecione uma referencia clinica.")
            return
        try:
            self.repository.review(
                self.selected_reference_id,
                self.status.currentText(),
                self.reviewer.text(),
                self.notes.toPlainText(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Governanca", str(exc))
            return
        self.audit_repository.log(
            self.current_user_id,
            "revisou_referencia_clinica",
            "referencias_clinicas",
            self.selected_reference_id,
            f"Status: {self.status.currentText()}; revisor: {self.reviewer.text()}",
        )
        self.refresh()
        QMessageBox.information(self, "Governanca", "Revisao registrada e auditada.")
