from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QTabWidget

from nutri_app.domain.food import Food
from nutri_app.domain.meal_plan import Meal
from nutri_app.repositories.advanced_clinical_repository import AdvancedClinicalRepository
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.repositories.meal_plan_repository import MealPlanRepository
from nutri_app.repositories.patient_allergy_repository import PatientAllergyRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.services.allergy_check import AllergyCheckService
from nutri_app.services.food import FoodService
from nutri_app.services.meal_plan import MealPlanService
from nutri_app.ui.pages.base import Page
from nutri_app.ui.pages.meal_plan_page_form_tab import MealPlanFormTabMixin
from nutri_app.ui.pages.meal_plan_page_smart_tab import SmartMealPlanTabMixin


class MealPlanPage(Page, MealPlanFormTabMixin, SmartMealPlanTabMixin):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Planejamento Alimentar", "Plano por refeicoes, itens e lista de compras.")
        self.repository = MealPlanRepository(connection_factory)
        self.smart_repository = AdvancedClinicalRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.food_repository = FoodRepository(connection_factory)
        self.food_service = FoodService()
        self.patient_allergy_repository = PatientAllergyRepository(connection_factory)
        self.allergy_check_service = AllergyCheckService()
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = MealPlanService()
        self.smart_definition = AdvancedClinicalService().by_module("Plano Inteligente")
        self.selected_plan_id: int | None = None
        self.selected_meal_index: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []
        self.smart_patient_ids_by_index: list[int | None] = []
        self.smart_inputs: dict[str, QLineEdit] = {}
        self.meals: list[Meal] = []
        self.selected_food_id: int | None = None
        self.foods_by_name: dict[str, Food] = {}

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_plan_tab(), "Plano alimentar")
        self.tabs.addTab(self._build_smart_plan_tab(), "Plano inteligente")

        self.layout.addWidget(self.tabs)
        self.refresh()

    def refresh(self) -> None:
        self._reload_foods()
        self._reload_patients()
        self._reload_plan_table()
        self._reload_smart_patients()
        self._reload_smart_table()
