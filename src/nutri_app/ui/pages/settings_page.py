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

from nutri_app.app.settings import AppSettings
from nutri_app.domain.backup import BackupStatus
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.backup_repository import BackupRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.services.backup import BackupService
from nutri_app.ui.date_format import format_datetime
from nutri_app.ui.pages.base import Page


class SettingsPage(Page):
    def __init__(
        self,
        settings: AppSettings,
        connection_factory: SQLiteConnectionFactory,
        user_repository: UserRepository,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Configuracoes", "Backup local, seguranca e auditoria.")
        self.settings = settings
        self.repository = BackupRepository(connection_factory)
        self.user_repository = user_repository
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = BackupService()
        self.selected_backup_id: int | None = None

        self.database_path = QLineEdit(str(settings.database_path))
        self.database_path.setReadOnly(True)
        self.backup_dir = QLineEdit(str(settings.database_path.parents[2] / "backups"))
        self.note = QLineEdit()
        self.security_panel = QTextEdit()
        self.security_panel.setReadOnly(True)
        self.security_panel.setFixedHeight(120)

        form = QFormLayout()
        form.addRow("Banco local", self.database_path)
        form.addRow("Diretorio backup", self.backup_dir)
        form.addRow("Observacoes", self.note)
        form.addRow("Painel seguranca", self.security_panel)

        create_backup = QPushButton("Criar backup")
        create_backup.setObjectName("primaryButton")
        create_backup.clicked.connect(self._create_backup)
        verify_backup = QPushButton("Verificar backup")
        verify_backup.clicked.connect(self._verify_backup)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)

        actions = QHBoxLayout()
        for button in [create_backup, verify_backup, refresh]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Arquivo", "Tamanho", "Checksum", "Status", "Criado em"]
        )
        self.table.cellClicked.connect(self._select_backup_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_table()
        self._reload_security_panel()

    def _create_backup(self) -> None:
        try:
            result = self.service.create_backup(
                self.settings.database_path,
                Path(self.backup_dir.text().strip()),
                self.note.text().strip(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Backup", str(exc))
            return

        backup_id = self.repository.add(result.record)
        self.audit_repository.log(
            self.current_user_id,
            "criou_backup",
            "backups_sistema",
            backup_id,
            result.record.file_path,
        )
        self.note.clear()
        self.refresh()
        QMessageBox.information(self, "Backup", result.message)

    def _verify_backup(self) -> None:
        if self.selected_backup_id is None:
            QMessageBox.warning(self, "Backup", "Selecione um backup para verificar.")
            return
        record = self.repository.get(self.selected_backup_id)
        if record is None:
            QMessageBox.warning(self, "Backup", "Backup nao encontrado.")
            self.refresh()
            return
        try:
            result = self.service.verify_backup(
                Path(record.file_path),
                record.checksum_sha256,
            )
        except ValueError as exc:
            self.repository.update_status(self.selected_backup_id, BackupStatus.FAILED, str(exc))
            QMessageBox.warning(self, "Backup", str(exc))
            self.refresh()
            return
        self.repository.update_status(
            self.selected_backup_id,
            result.record.status,
            result.record.notes,
        )
        self.audit_repository.log(
            self.current_user_id,
            "verificou_backup",
            "backups_sistema",
            self.selected_backup_id,
            record.file_path,
        )
        self.refresh()
        QMessageBox.information(self, "Backup", result.message)

    def _reload_table(self) -> None:
        records = self.repository.list_active()
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.file_path))
            self.table.setItem(row, 2, QTableWidgetItem(str(record.size_bytes)))
            self.table.setItem(row, 3, QTableWidgetItem(record.checksum_sha256[:16]))
            self.table.setItem(row, 4, QTableWidgetItem(record.status.value))
            created_at = format_datetime(record.created_at)
            self.table.setItem(row, 5, QTableWidgetItem(created_at))

    def _select_backup_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        self.selected_backup_id = int(item.text())

    def _reload_security_panel(self) -> None:
        active_users = self.user_repository.count_users()
        total_permissions = self.repository.count_permissions()
        checklist = self.service.security_checklist(active_users, total_permissions)
        self.security_panel.setPlainText("\n".join(f"- {item}" for item in checklist))
