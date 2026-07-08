from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nutri_app.app.context import AppContext
from nutri_app.domain.user import AuthenticatedUser
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.ui.pages.advanced_module_page import AdvancedModulePage
from nutri_app.ui.pages.ai_assistant_page import AIAssistantPage
from nutri_app.ui.pages.anamnesis_page import AnamnesisPage
from nutri_app.ui.pages.anthropometry_page import AnthropometryPage
from nutri_app.ui.pages.appointments_page import AppointmentsPage
from nutri_app.ui.pages.body_composition_page import BodyCompositionPage
from nutri_app.ui.pages.dashboard_page import DashboardPage
from nutri_app.ui.pages.deployment_page import DeploymentPage
from nutri_app.ui.pages.energy_expenditure_page import EnergyExpenditurePage
from nutri_app.ui.pages.finance_page import FinancePage
from nutri_app.ui.pages.food_database_page import FoodDatabasePage
from nutri_app.ui.pages.integrations_page import IntegrationsPage
from nutri_app.ui.pages.laboratory_exams_page import LaboratoryExamsPage
from nutri_app.ui.pages.meal_plan_page import MealPlanPage
from nutri_app.ui.pages.nutrition_diagnosis_page import NutritionDiagnosisPage
from nutri_app.ui.pages.patient_app_page import PatientAppPage
from nutri_app.ui.pages.patients_page import PatientsPage
from nutri_app.ui.pages.recipes_page import RecipesPage
from nutri_app.ui.pages.reports_page import ReportsPage
from nutri_app.ui.pages.screening_page import ScreeningPage
from nutri_app.ui.pages.settings_page import SettingsPage
from nutri_app.ui.pages.supplements_page import SupplementsPage
from nutri_app.ui.pages.users_page import UsersPage
from nutri_app.ui.pages.web_portal_page import WebPortalPage


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

        self.menu = QTreeWidget()
        self.menu.setFixedWidth(280)
        self.menu.setHeaderHidden(True)
        self.menu.setIndentation(18)
        self.menu.setAnimated(True)
        self.menu.itemClicked.connect(self._change_page)

        self.pages = QStackedWidget()
        navigation_items = self._navigation_items()
        self.page_indexes_by_module: dict[str, int] = {}
        for item in navigation_items:
            page_index = self.pages.count()
            self.pages.addWidget(item.page)
            self.page_indexes_by_module[item.module] = page_index

        self._populate_menu(navigation_items)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._sidebar())
        layout.addWidget(self.pages, stretch=1)
        self.setCentralWidget(root)

    def _navigation_items(self) -> list[NavigationItem]:
        advanced_service = AdvancedClinicalService()
        advanced_definitions = {
            definition.module: definition
            for definition in advanced_service.definitions()
        }
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
                "Aplicativo Paciente",
                "Aplicativo Paciente",
                PatientAppPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Portal Web",
                "Portal Web",
                WebPortalPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "IA Assistiva",
                "IA Assistiva",
                AIAssistantPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Anamnese Avancada",
                "Anamnese Avancada",
                AdvancedModulePage(
                    advanced_definitions["Anamnese Avancada"],
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Exames Avancados",
                "Exames Avancados",
                AdvancedModulePage(
                    advanced_definitions["Exames Avancados"],
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Protocolos Clinicos",
                "Protocolos Clinicos",
                AdvancedModulePage(
                    advanced_definitions["Protocolos Clinicos"],
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Pediatria",
                "Pediatria",
                AdvancedModulePage(
                    advanced_definitions["Pediatria"],
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Nefrologia",
                "Nefrologia",
                AdvancedModulePage(
                    advanced_definitions["Nefrologia"],
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Terapia Nutricional",
                "Terapia Nutricional",
                AdvancedModulePage(
                    advanced_definitions["Terapia Nutricional"],
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Integracoes",
                "Integracoes",
                IntegrationsPage(
                    self.context.connection_factory,
                    self.context.audit_repository,
                    self.current_user.id,
                ),
            ),
            NavigationItem(
                "Implantacao",
                "Implantacao",
                DeploymentPage(
                    self.context.settings,
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
        visible_items = [
            item
            for item in items
            if self.context.user_repository.can_view_module(self.current_user.role, item.module)
        ]
        return visible_items

    def _populate_menu(self, navigation_items: list[NavigationItem]) -> None:
        items_by_module = {item.module: item for item in navigation_items}

        self._add_leaf(self.menu, "🏠 Dashboard", "Dashboard", items_by_module)
        self._add_leaf(self.menu, "👥 Pacientes", "Pacientes", items_by_module)

        clinical = self._add_group("🩺 Atendimento Clinico")
        self._add_leaf(clinical, "Agenda", "Agenda", items_by_module)
        self._add_leaf(clinical, "Anamnese", "Anamnese", items_by_module)
        self._add_leaf(clinical, "Anamnese Avancada", "Anamnese Avancada", items_by_module)

        body = self._add_group("Avaliacao Corporal", clinical)
        self._add_leaf(body, "Antropometria", "Antropometria", items_by_module)
        self._add_leaf(body, "Composicao Corporal", "Composicao Corporal", items_by_module)
        self._add_leaf(body, "Gasto Energetico", "Gasto Energetico", items_by_module)
        self._remove_empty_group(body)

        protocols = self._add_group("Diagnostico & Protocolos", clinical)
        self._add_leaf(protocols, "Diagnostico", "Diagnostico", items_by_module)
        self._add_leaf(protocols, "Protocolos Clinicos", "Protocolos Clinicos", items_by_module)
        self._add_leaf(protocols, "Triagem Nutricional", "Triagem Nutricional", items_by_module)
        self._remove_empty_group(protocols)

        exams = self._add_group("Exames", clinical)
        self._add_leaf(exams, "Exames", "Exames", items_by_module)
        self._add_leaf(exams, "Exames Avancados", "Exames Avancados", items_by_module)
        self._remove_empty_group(exams)

        specialties = self._add_group("Especialidades", clinical)
        self._add_leaf(specialties, "Nefrologia", "Nefrologia", items_by_module)
        self._add_leaf(specialties, "Pediatria", "Pediatria", items_by_module)
        self._add_leaf(specialties, "Terapia Nutricional", "Terapia Nutricional", items_by_module)
        self._remove_empty_group(specialties)

        self._add_leaf(clinical, "IA Assistiva", "IA Assistiva", items_by_module)
        self._add_leaf(clinical, "Plano Alimentar", "Plano Alimentar", items_by_module)
        self._add_leaf(clinical, "Relatorios", "Relatorios", items_by_module)
        self._remove_empty_group(clinical)

        foods = self._add_group("🍎 Banco de Alimentos")
        self._add_leaf(foods, "Banco de Alimentos", "Banco de Alimentos", items_by_module)
        self._add_leaf(foods, "Receitas", "Receitas", items_by_module)
        self._add_leaf(foods, "Suplementos", "Suplementos", items_by_module)
        self._remove_empty_group(foods)

        channels = self._add_group("📱 Canais do Paciente")
        self._add_leaf(channels, "Aplicativo Paciente", "Aplicativo Paciente", items_by_module)
        self._add_leaf(channels, "Portal Web", "Portal Web", items_by_module)
        self._remove_empty_group(channels)

        self._add_leaf(self.menu, "💰 Financeiro", "Financeiro", items_by_module)

        settings = self._add_group("⚙️ Configuracoes")
        self._add_leaf(settings, "Configuracoes", "Configuracoes", items_by_module)
        self._add_leaf(settings, "Implantacao", "Implantacao", items_by_module)
        self._add_leaf(settings, "Integracoes", "Integracoes", items_by_module)
        self._add_leaf(settings, "Usuarios", "Usuarios", items_by_module)
        self._remove_empty_group(settings)

        dashboard = self._find_item_by_module("Dashboard")
        if dashboard is not None:
            self.menu.setCurrentItem(dashboard)
            self._show_page(dashboard)

    def _add_group(
        self,
        title: str,
        parent: QTreeWidget | QTreeWidgetItem | None = None,
    ) -> QTreeWidgetItem:
        group = QTreeWidgetItem([title])
        group.setToolTip(0, title)
        group.setTextAlignment(0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        group.setData(0, Qt.ItemDataRole.UserRole, None)
        group.setExpanded(False)
        if parent is None:
            self.menu.addTopLevelItem(group)
        else:
            parent.addChild(group)
        return group

    def _add_leaf(
        self,
        parent: QTreeWidget | QTreeWidgetItem,
        title: str,
        module: str,
        items_by_module: dict[str, NavigationItem],
    ) -> QTreeWidgetItem | None:
        if module not in items_by_module:
            return None

        leaf = QTreeWidgetItem([title])
        leaf.setToolTip(0, title)
        leaf.setTextAlignment(0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        leaf.setData(0, Qt.ItemDataRole.UserRole, self.page_indexes_by_module[module])
        leaf.setData(0, Qt.ItemDataRole.UserRole + 1, module)
        if isinstance(parent, QTreeWidget):
            parent.addTopLevelItem(leaf)
        else:
            parent.addChild(leaf)
        return leaf

    def _remove_empty_group(self, group: QTreeWidgetItem) -> None:
        if group.childCount() > 0:
            return
        parent = group.parent()
        if parent is None:
            index = self.menu.indexOfTopLevelItem(group)
            if index >= 0:
                self.menu.takeTopLevelItem(index)
            return
        parent.removeChild(group)

    def _find_item_by_module(self, module: str) -> QTreeWidgetItem | None:
        items = self.menu.findItems("", Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive)
        for item in items:
            if item.data(0, Qt.ItemDataRole.UserRole + 1) == module:
                return item
        return None

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

    def _change_page(self, item: QTreeWidgetItem, _column: int) -> None:
        page_index = item.data(0, Qt.ItemDataRole.UserRole)
        if page_index is None:
            item.setExpanded(not item.isExpanded())
            return
        self._show_page(item)

    def _show_page(self, item: QTreeWidgetItem) -> None:
        page_index = item.data(0, Qt.ItemDataRole.UserRole)
        if page_index is None:
            return
        self.pages.setCurrentIndex(int(page_index))
        page = self.pages.currentWidget()
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            refresh()
