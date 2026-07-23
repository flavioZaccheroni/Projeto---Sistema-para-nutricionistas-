from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
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
        self.portal_title = QLineEdit("Nutri Clinic Pro")
        self.portal_subtitle = QLineEdit()
        self.portal_subtitle.setPlaceholderText("Entre a exploracao subtitulo")
        self.environment = QComboBox()
        self.environment.addItems(["Teste", "Producao"])
        self.publish_mode = QButtonGroup(self)
        self.manual_mode = QRadioButton("Manual")
        self.ftp_mode = QRadioButton("Automatica via FTP")
        self.manual_mode.setChecked(True)
        self.publish_mode.addButton(self.manual_mode)
        self.publish_mode.addButton(self.ftp_mode)
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setFixedHeight(112)

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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(14)
        wrapper_layout.addWidget(self._output_card())
        middle = QWidget()
        middle_layout = QGridLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setHorizontalSpacing(14)
        middle_layout.addWidget(self._generation_card(), 0, 0)
        middle_layout.addWidget(self._status_card(), 0, 1)
        middle_layout.setColumnStretch(0, 1)
        middle_layout.setColumnStretch(1, 1)
        wrapper_layout.addWidget(middle)
        wrapper_layout.addLayout(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self._history_card())
        self.refresh()

    def _output_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Diretorio de saida", self.output_dir)
        return card

    def _generation_card(self) -> QGroupBox:
        card = QGroupBox("Geracao e Publicacao")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Titulo do Portal", self.portal_title)
        self._add_stacked_field(layout, 0, "Subtitulo", self.portal_subtitle, column=1)
        self._add_stacked_field(layout, 2, "Ambiente", self.environment)
        mode_widget = QWidget()
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.addWidget(self.manual_mode)
        mode_layout.addWidget(self.ftp_mode)
        self._add_stacked_field(layout, 2, "Modo de Publicacao", mode_widget, column=1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return card

    def _status_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        self._add_stacked_field(layout, 0, "Status", self.status)
        return card

    def _history_card(self) -> QGroupBox:
        card = QGroupBox("Geracoes Anteriores")
        layout = QVBoxLayout(card)
        layout.addWidget(self.table)
        return card

    def _add_stacked_field(
        self,
        layout: QGridLayout,
        row: int,
        label: str,
        widget: QWidget,
        column: int = 0,
    ) -> None:
        title = QLabel(label)
        title.setObjectName("miniHeader")
        layout.addWidget(title, row, column)
        layout.addWidget(widget, row + 1, column)

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
        mode = "Manual" if self.manual_mode.isChecked() else "Automatica via FTP"
        title = self.portal_title.text().strip() or "Portal Web Nutri Clinic Pro"
        snapshot = self.repository.build_snapshot()
        total_pages = self.service.publish_static_portal(snapshot, output)
        record_id = self.repository.add_publish_record(
            WebPortalPublishRecord(
                title=f"{title} ({mode})",
                output_path=str(output),
                status=f"Gerado - {self.environment.currentText()}",
                total_pages=total_pages,
                notes=self.portal_subtitle.text().strip()
                or "Portal web estatico gerado pela fase 22.",
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
            f"Portal gerado com {total_pages} paginas.\n"
            f"Ambiente: {self.environment.currentText()}\n"
            f"Modo: {mode}\n"
            f"Arquivo inicial: {output / 'index.html'}"
        )
        self.refresh()
        QMessageBox.information(self, "Portal Web", "Portal web gerado com sucesso.")
