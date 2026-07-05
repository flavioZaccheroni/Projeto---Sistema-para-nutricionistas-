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

from nutri_app.domain.web_portal import WebPortalPublishRecord
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.web_portal_repository import WebPortalRepository
from nutri_app.services.web_portal import WebPortalService
from nutri_app.ui.pages.base import Page


class WebPortalPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Portal Web",
            "Geracao inicial de portal web estatico para operacao e homologacao.",
        )
        self.repository = WebPortalRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = WebPortalService()

        root = Path(__file__).resolve().parents[4]
        self.output_dir = QLineEdit(str(root / "exports" / "portal_web"))
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Diretorio de saida", self.output_dir)
        form.addRow("Status", self.status)

        publish = QPushButton("Gerar portal")
        publish.setObjectName("primaryButton")
        publish.clicked.connect(self._publish)
        refresh = QPushButton("Atualizar historico")
        refresh.clicked.connect(self.refresh)

        actions = QHBoxLayout()
        actions.addWidget(publish)
        actions.addWidget(refresh)
        actions.addStretch()

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Titulo", "Saida", "Status", "Paginas"])

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        records = self.repository.list_publish_records()
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.title))
            self.table.setItem(row, 2, QTableWidgetItem(record.output_path))
            self.table.setItem(row, 3, QTableWidgetItem(record.status))
            self.table.setItem(row, 4, QTableWidgetItem(str(record.total_pages)))

    def _publish(self) -> None:
        output = Path(self.output_dir.text().strip())
        snapshot = self.repository.build_snapshot()
        total_pages = self.service.publish_static_portal(snapshot, output)
        record_id = self.repository.add_publish_record(
            WebPortalPublishRecord(
                title="Portal Web Nutri Clinic Pro",
                output_path=str(output),
                status="Gerado",
                total_pages=total_pages,
                notes="Portal web estatico gerado pela fase 22.",
            )
        )
        self.audit_repository.log(
            self.current_user_id,
            "gerou_portal_web",
            "portal_web_publicacoes",
            record_id,
            str(output),
        )
        self.status.setPlainText(
            f"Portal gerado com {total_pages} paginas.\nArquivo inicial: {output / 'index.html'}"
        )
        self.refresh()
        QMessageBox.information(self, "Portal Web", "Portal web gerado com sucesso.")
