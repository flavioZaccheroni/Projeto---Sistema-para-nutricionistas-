from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nutri_app.app.settings import AppSettings
from nutri_app.database.schema import initialize_database
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.anamnesis_page import AnamnesisPage
from nutri_app.ui.pages.anthropometry_page import AnthropometryPage
from nutri_app.ui.pages.dashboard_page import DashboardPage
from nutri_app.ui.pages.patients_page import PatientsPage
from nutri_app.ui.pages.reports_page import ReportsPage


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.setWindowTitle(settings.app_name)
        self.resize(1200, 760)

        connection_factory = SQLiteConnectionFactory(settings.database_path)
        initialize_database(connection_factory)

        self.menu = QListWidget()
        self.menu.setFixedWidth(240)
        self.menu.setSpacing(4)
        self.menu.currentRowChanged.connect(self._change_page)

        self.pages = QStackedWidget()
        self.pages.addWidget(DashboardPage())
        self.pages.addWidget(PatientsPage(connection_factory))
        self.pages.addWidget(AnamnesisPage())
        self.pages.addWidget(AnthropometryPage())
        self.pages.addWidget(ReportsPage())

        for title in ["Dashboard", "Pacientes", "Anamnese", "Antropometria", "Relatorios"]:
            item = QListWidgetItem(title)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.menu.addItem(item)

        self.menu.setCurrentRow(0)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._sidebar())
        layout.addWidget(self.pages, stretch=1)
        self.setCentralWidget(root)

    def _sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        title = QLabel("Nutri Clinic Pro")
        title.setObjectName("appTitle")
        title.setMargin(16)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(self.menu)
        return sidebar

    def _change_page(self, index: int) -> None:
        if index >= 0:
            self.pages.setCurrentIndex(index)
