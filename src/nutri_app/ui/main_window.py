from __future__ import annotations

from dataclasses import dataclass

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

from nutri_app.app.context import AppContext
from nutri_app.ui.pages.anamnesis_page import AnamnesisPage
from nutri_app.ui.pages.anthropometry_page import AnthropometryPage
from nutri_app.ui.pages.dashboard_page import DashboardPage
from nutri_app.ui.pages.module_placeholder_page import ModulePlaceholderPage
from nutri_app.ui.pages.patients_page import PatientsPage
from nutri_app.ui.pages.reports_page import ReportsPage


@dataclass(frozen=True)
class NavigationItem:
    title: str
    page: QWidget


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.setWindowTitle(context.settings.app_name)
        self.resize(1200, 760)

        self.menu = QListWidget()
        self.menu.setFixedWidth(240)
        self.menu.setSpacing(4)
        self.menu.currentRowChanged.connect(self._change_page)

        self.pages = QStackedWidget()
        for item in self._navigation_items():
            self.pages.addWidget(item.page)
            menu_item = QListWidgetItem(item.title)
            menu_item.setToolTip(item.title)
            menu_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.menu.addItem(menu_item)

        self.menu.setCurrentRow(0)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._sidebar())
        layout.addWidget(self.pages, stretch=1)
        self.setCentralWidget(root)

    def _navigation_items(self) -> list[NavigationItem]:
        return [
            NavigationItem("Dashboard", DashboardPage()),
            NavigationItem("Pacientes", PatientsPage(self.context.connection_factory)),
            NavigationItem(
                "Agenda",
                ModulePlaceholderPage(
                    "Agenda e Consultas",
                    "Marcacao, retorno, cancelamentos e historico de atendimento.",
                    "Fase 6",
                    ["Agenda diaria", "Consulta inicial", "Retornos", "Pendencias"],
                ),
            ),
            NavigationItem("Anamnese", AnamnesisPage()),
            NavigationItem(
                "Triagem Nutricional",
                ModulePlaceholderPage(
                    "Triagem Nutricional",
                    "Protocolos e classificacao automatica de risco nutricional.",
                    "Fase 8",
                    ["NRS-2002", "MUST", "MST", "MNA", "STRONGkids", "MIS"],
                ),
            ),
            NavigationItem("Antropometria", AnthropometryPage()),
            NavigationItem(
                "Exames",
                ModulePlaceholderPage(
                    "Exames Laboratoriais",
                    "Cadastro, interpretacao assistida e alertas clinicos.",
                    "Fase 12",
                    ["Hemograma", "Perfil glicemico", "Funcao renal", "Perfil lipidico"],
                ),
            ),
            NavigationItem(
                "Diagnostico",
                ModulePlaceholderPage(
                    "Diagnostico Nutricional",
                    "Classificacoes baseadas em protocolos clinicos.",
                    "Fase 13",
                    ["GLIM", "ASPEN", "ESPEN", "BRASPEN", "Sarcopenia"],
                ),
            ),
            NavigationItem(
                "Plano Alimentar",
                ModulePlaceholderPage(
                    "Planejamento Alimentar",
                    "Cardapio, substituicoes, receitas e lista de compras.",
                    "Fase 14",
                    ["Distribuicao por refeicoes", "Plano semanal", "Lista de compras"],
                ),
            ),
            NavigationItem("Relatorios", ReportsPage()),
            NavigationItem(
                "Financeiro",
                ModulePlaceholderPage(
                    "Financeiro",
                    "Pagamentos, recebimentos, inadimplencia e relatorios.",
                    "Fase 19",
                    ["Planos", "Pagamentos", "Relatorio mensal"],
                ),
            ),
            NavigationItem(
                "Configuracoes",
                ModulePlaceholderPage(
                    "Configuracoes",
                    "Parametros gerais, backup, seguranca e identidade da clinica.",
                    "Fase 20",
                    ["Backup", "Permissoes", "Identidade dos relatorios"],
                ),
            ),
        ]

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
