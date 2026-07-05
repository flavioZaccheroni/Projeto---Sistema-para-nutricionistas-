from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
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
from nutri_app.domain.user import AuthenticatedUser
from nutri_app.ui.pages.anamnesis_page import AnamnesisPage
from nutri_app.ui.pages.anthropometry_page import AnthropometryPage
from nutri_app.ui.pages.appointments_page import AppointmentsPage
from nutri_app.ui.pages.body_composition_page import BodyCompositionPage
from nutri_app.ui.pages.dashboard_page import DashboardPage
from nutri_app.ui.pages.energy_expenditure_page import EnergyExpenditurePage
from nutri_app.ui.pages.finance_page import FinancePage
from nutri_app.ui.pages.food_database_page import FoodDatabasePage
from nutri_app.ui.pages.laboratory_exams_page import LaboratoryExamsPage
from nutri_app.ui.pages.meal_plan_page import MealPlanPage
from nutri_app.ui.pages.nutrition_diagnosis_page import NutritionDiagnosisPage
from nutri_app.ui.pages.patients_page import PatientsPage
from nutri_app.ui.pages.recipes_page import RecipesPage
from nutri_app.ui.pages.reports_page import ReportsPage
from nutri_app.ui.pages.screening_page import ScreeningPage
from nutri_app.ui.pages.settings_page import SettingsPage
from nutri_app.ui.pages.supplements_page import SupplementsPage
from nutri_app.ui.pages.users_page import UsersPage


@dataclass(frozen=True)
class NavigationItem:
    title: str
    module: str
    page: QWidget


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext, current_user: AuthenticatedUser) -> None:
        super().__init__()
        self.context = context
        self.current_user = current_user
        self.setWindowTitle(context.settings.app_name)
        if context.settings.icon_path.exists():
            self.setWindowIcon(QIcon(str(context.settings.icon_path)))
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
        items = [
            NavigationItem(
                "Dashboard",
                "Dashboard",
                DashboardPage(self.context.connection_factory),
            ),
            NavigationItem(
                "Usuarios",
                "Usuarios",
                UsersPage(
                    self.context.user_repository,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Pacientes",
                "Pacientes",
                PatientsPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Agenda",
                "Agenda",
                AppointmentsPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Anamnese",
                "Anamnese",
                AnamnesisPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Triagem Nutricional",
                "Triagem Nutricional",
                ScreeningPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Antropometria",
                "Antropometria",
                AnthropometryPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Composicao Corporal",
                "Composicao Corporal",
                BodyCompositionPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Gasto Energetico",
                "Gasto Energetico",
                EnergyExpenditurePage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Exames",
                "Exames",
                LaboratoryExamsPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Diagnostico",
                "Diagnostico",
                NutritionDiagnosisPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Plano Alimentar",
                "Plano Alimentar",
                MealPlanPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Banco de Alimentos",
                "Banco de Alimentos",
                FoodDatabasePage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Receitas",
                "Receitas",
                RecipesPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Suplementos",
                "Suplementos",
                SupplementsPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Relatorios",
                "Relatorios",
                ReportsPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Financeiro",
                "Financeiro",
                FinancePage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Configuracoes",
                "Configuracoes",
                SettingsPage(
                    self.context.settings,
                    self.context.connection_factory,
                    self.context.user_repository,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
        ]
        return [
            item
            for item in items
            if self.context.user_repository.can_view_module(self.current_user.role, item.module)
        ]

    def _sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        title = QLabel("Nutri Clinic Pro")
        title.setObjectName("appTitle")
        title.setMargin(16)
        user = QLabel(f"{self.current_user.name}\n{self.current_user.role.value}")
        user.setObjectName("currentUser")
        user.setMargin(16)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(user)
        layout.addWidget(self.menu)
        return sidebar

    def _change_page(self, index: int) -> None:
        if index >= 0:
            self.pages.setCurrentIndex(index)
            page = self.pages.currentWidget()
            refresh = getattr(page, "refresh", None)
            if callable(refresh):
                refresh()
