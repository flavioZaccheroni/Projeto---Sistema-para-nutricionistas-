from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.domain.meal_plan import Meal, MealPlan, MealPlanItem
from nutri_app.repositories.advanced_clinical_repository import AdvancedClinicalRepository
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.meal_plan_repository import MealPlanRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.services.meal_plan import MealPlanService
from nutri_app.ui.date_format import (
    format_date,
    format_datetime,
    parse_date,
    parse_optional_date,
    today_text,
)
from nutri_app.ui.pages.base import Page


class MealPlanPage(Page):
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

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_plan_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("mm-dd-aaaa")
        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText("mm-dd-aaaa opcional")
        self.objective = QLineEdit()
        self.target_energy = QLineEdit()
        self.target_protein = QLineEdit()
        self.target_carbohydrate = QLineEdit()
        self.target_fat = QLineEdit()
        self.total_energy = QLineEdit()
        self.total_energy.setReadOnly(True)
        self.total_protein = QLineEdit()
        self.total_protein.setReadOnly(True)
        self.total_carbohydrate = QLineEdit()
        self.total_carbohydrate.setReadOnly(True)
        self.total_fat = QLineEdit()
        self.total_fat.setReadOnly(True)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(55)

        self.meal_name = QLineEdit()
        self.meal_time = QLineEdit()
        self.meal_notes = QLineEdit()
        self.food = QLineEdit()
        self.quantity = QLineEdit()
        self.unit = QLineEdit()
        self.energy = QLineEdit()
        self.protein = QLineEdit()
        self.carbohydrate = QLineEdit()
        self.fat = QLineEdit()
        self.substitutions = QLineEdit()
        self.shopping_list = QTextEdit()
        self.shopping_list.setReadOnly(True)
        self.shopping_list.setFixedHeight(75)

        meal_form = QFormLayout()
        meal_form.addRow("Refeicao", self.meal_name)
        meal_form.addRow("Horario", self.meal_time)
        meal_form.addRow("Obs. refeicao", self.meal_notes)
        meal_form.addRow("Alimento", self.food)
        meal_form.addRow("Quantidade", self.quantity)
        meal_form.addRow("Unidade", self.unit)
        meal_form.addRow("Kcal", self.energy)
        meal_form.addRow("Proteina (g)", self.protein)
        meal_form.addRow("Carboidrato (g)", self.carbohydrate)
        meal_form.addRow("Lipidios (g)", self.fat)
        meal_form.addRow("Substituicoes", self.substitutions)
        meal_form.addRow("Lista de compras", self.shopping_list)

        add_meal = QPushButton("Adicionar refeicao")
        add_meal.clicked.connect(self._add_meal)
        add_item = QPushButton("Adicionar item")
        add_item.clicked.connect(self._add_item)
        remove_meal = QPushButton("Remover refeicao")
        remove_meal.clicked.connect(self._remove_meal)
        calculate = QPushButton("Calcular")
        calculate.clicked.connect(self._calculate_totals)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_plan)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_plan)

        actions = QHBoxLayout()
        for button in [add_meal, add_item, remove_meal, calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.meal_table = QTableWidget(0, 6)
        self.meal_table.setHorizontalHeaderLabels(
            ["Refeicao", "Horario", "Itens", "Kcal", "Proteina", "Carboidrato"]
        )
        self.meal_table.cellClicked.connect(self._select_meal_from_table)
        self._configure_table(self.meal_table)

        self.plan_table = QTableWidget(0, 7)
        self.plan_table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Inicio", "Objetivo", "Kcal", "Proteina", "Refeicoes"]
        )
        self.plan_table.cellClicked.connect(self._select_plan_from_table)
        self._configure_table(self.plan_table)

        plan_tab = QWidget()
        plan_layout = QVBoxLayout(plan_tab)
        plan_layout.addWidget(self._plan_header_card())
        section_title = QLabel("Resumo do Plano")
        section_title.setObjectName("sectionTitle")
        plan_layout.addWidget(section_title)
        self.meal_cards = QWidget()
        self.meal_cards_layout = QGridLayout(self.meal_cards)
        self.meal_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.meal_cards_layout.setHorizontalSpacing(14)
        plan_layout.addWidget(self.meal_cards)
        add_meal_panel = QPushButton("+\nAdicionar nova refeicao")
        add_meal_panel.setObjectName("addMealPanel")
        add_meal_panel.clicked.connect(self._add_meal)
        plan_layout.addWidget(add_meal_panel)
        plan_layout.addWidget(self._form_card("Cadastro de Refeicao e Itens", meal_form))
        plan_layout.addLayout(actions)
        plan_layout.addWidget(self.meal_table)
        plan_layout.addWidget(self.plan_table)

        tabs = QTabWidget()
        tabs.addTab(plan_tab, "Plano alimentar")
        tabs.addTab(self._build_smart_plan_tab(), "Plano inteligente")

        self.layout.addWidget(tabs)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_plan_table()
        self._reload_smart_patients()
        self._reload_smart_table()

    def _build_smart_plan_tab(self) -> QWidget:
        self.smart_patient = QComboBox()
        self.smart_record_date = QLineEdit(today_text())
        self.smart_record_date.setPlaceholderText("mm-dd-aaaa")
        self.smart_profile = QComboBox()
        self.smart_profile.addItems(self.smart_definition.profiles)
        self.smart_notes = QTextEdit()
        self.smart_notes.setFixedHeight(70)
        self.smart_result = QTextEdit()
        self.smart_result.setReadOnly(True)
        self.smart_result.setFixedHeight(110)

        for key, _label in self.smart_definition.fields:
            self.smart_inputs[key] = QLineEdit()

        calculate = QPushButton("Calcular / salvar")
        calculate.setObjectName("primaryButton")
        calculate.clicked.connect(self._save_smart_plan)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self._clear_smart_plan)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self._reload_smart_table)

        actions = QHBoxLayout()
        for button in [calculate, clear, refresh]:
            actions.addWidget(button)
        actions.addStretch()

        self.smart_table = QTableWidget(0, 6)
        self.smart_table.setHorizontalHeaderLabels(
            ["ID", "Data", "Paciente", "Perfil", "Resultado", "Observacoes"]
        )
        self._configure_table(self.smart_table)

        tab = QWidget()
        layout = QGridLayout(tab)
        layout.addWidget(self._smart_profile_card(), 0, 0)
        layout.addWidget(self._smart_macros_card(), 1, 0)
        layout.addWidget(self._smart_result_card(), 0, 1, 2, 1)
        layout.addLayout(actions, 2, 0, 1, 2)
        layout.addWidget(self.smart_table, 3, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return tab

    def _form_card(self, title: str, form: QFormLayout) -> QGroupBox:
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        layout.addLayout(form)
        return card

    def _plan_header_card(self) -> QGroupBox:
        card = QGroupBox("")
        layout = QGridLayout(card)
        left_fields = [
            ("Pesquisar", self.search),
            ("Paciente", self.patient),
            ("Consulta vinculada", self.appointment),
            ("Data inicio", self.start_date),
            ("Data fim", self.end_date),
            ("Objetivo", self.objective),
        ]
        right_fields = [
            ("Meta kcal", self.target_energy),
            ("Meta proteina (g)", self.target_protein),
            ("Meta carboidrato (g)", self.target_carbohydrate),
            ("Meta lipidios (g)", self.target_fat),
            ("Total kcal", self.total_energy),
            ("Total proteina (g)", self.total_protein),
            ("Total carboidrato (g)", self.total_carbohydrate),
            ("Total lipidios (g)", self.total_fat),
        ]
        for row, (label, widget) in enumerate(left_fields):
            layout.addWidget(QLabel(label), row, 0)
            layout.addWidget(widget, row, 1)
        for row, (label, widget) in enumerate(right_fields):
            layout.addWidget(QLabel(label), row, 2)
            layout.addWidget(widget, row, 3)
        layout.addWidget(QLabel("Observacoes"), 6, 0)
        layout.addWidget(self.notes, 6, 1, 1, 3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        return card

    def _smart_profile_card(self) -> QGroupBox:
        card = QGroupBox("Paciente e Perfil")
        layout = QGridLayout(card)
        layout.addWidget(QLabel("Paciente"), 0, 0)
        layout.addWidget(self.smart_patient, 1, 0)
        layout.addWidget(QLabel("Data"), 0, 1)
        layout.addWidget(self.smart_record_date, 1, 1)
        layout.addWidget(QLabel("Perfil"), 0, 2)
        layout.addWidget(self.smart_profile, 1, 2)
        return card

    def _smart_macros_card(self) -> QGroupBox:
        card = QGroupBox("Macronutrientes e Restricoes")
        layout = QGridLayout(card)
        fields = [
            ("energy", "Energia (kcal)"),
            ("protein", "Proteina (g)"),
            ("carbohydrate", "Carboidrato (g)"),
            ("fat", "Lipidios (g)"),
            ("meals", "Numero de refeicoes"),
            ("restrictions", "Restricoes/Preferencias"),
        ]
        for index, (key, label) in enumerate(fields):
            row = (index // 2) * 2
            column = index % 2
            layout.addWidget(QLabel(label), row, column)
            layout.addWidget(self.smart_inputs[key], row + 1, column)
        layout.addWidget(QLabel("Observacoes"), 6, 0)
        layout.addWidget(self.smart_notes, 7, 0, 1, 2)
        return card

    def _smart_result_card(self) -> QGroupBox:
        card = QGroupBox("Resultados Gerados")
        layout = QVBoxLayout(card)
        layout.addWidget(self.smart_result)
        return card

    def _configure_table(self, table: QTableWidget) -> None:
        table.setWordWrap(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _meal_summary_card(self, meal: Meal, index: int) -> QGroupBox:
        energy, protein, carbohydrate, fat = self.service.calculate_totals([meal])
        card = QGroupBox(meal.name or f"Refeicao {index + 1}")
        layout = QGridLayout(card)
        layout.addWidget(QLabel("Horario"), 0, 0)
        layout.addWidget(QLabel(meal.time or "-"), 0, 1)
        layout.addWidget(QLabel("Obs. Refeicao"), 1, 0)
        notes = QLineEdit(meal.notes)
        notes.setReadOnly(True)
        layout.addWidget(notes, 1, 1, 1, 3)
        headers = ["Quantidade", "Unidade", "Kcal", "P/C/L"]
        for column, header in enumerate(headers):
            label = QLabel(header)
            label.setObjectName("miniHeader")
            layout.addWidget(label, 2, column)
        if meal.items:
            first_item = meal.items[0]
            values = [
                f"{first_item.quantity:g}",
                first_item.unit or "-",
                f"{first_item.energy_kcal:.0f}",
                f"{first_item.protein_g:.1f}/{first_item.carbohydrate_g:.1f}/{first_item.fat_g:.1f}",
            ]
        else:
            values = ["-", "-", f"{energy:.0f}", f"{protein:.1f}/{carbohydrate:.1f}/{fat:.1f}"]
        for column, value in enumerate(values):
            layout.addWidget(QLabel(value), 3, column)
        select = QPushButton("Selecionar")
        select.clicked.connect(
            lambda _checked=False, row=index: self._select_meal_from_table(row, 0)
        )
        layout.addWidget(select, 4, 0, 1, 4)
        return card

    def _refresh_meal_cards(self) -> None:
        if not hasattr(self, "meal_cards_layout"):
            return
        while self.meal_cards_layout.count():
            item = self.meal_cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not self.meals:
            empty = QLabel("Nenhuma refeicao adicionada.")
            empty.setObjectName("mutedText")
            self.meal_cards_layout.addWidget(empty, 0, 0)
            self.meal_cards_layout.setColumnStretch(0, 1)
            return
        for index, meal in enumerate(self.meals[:4]):
            self.meal_cards_layout.addWidget(self._meal_summary_card(meal, index), 0, index)
            self.meal_cards_layout.setColumnStretch(index, 1)
        if len(self.meals) > 4:
            more = QLabel(f"+ {len(self.meals) - 4} refeicao(oes) na tabela abaixo")
            more.setObjectName("mutedText")
            self.meal_cards_layout.addWidget(more, 1, 0, 1, 4)

    def _save_plan(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Plano alimentar", "Cadastre um paciente antes do plano.")
            return

        try:
            plan = self._build_plan()
            self.service.validate_plan(plan)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if plan.id is None:
            plan_id = self.repository.add(plan)
            self._audit("criou_plano_alimentar", plan_id, "Plano alimentar criado.")
        else:
            self.repository.update(plan)
            plan_id = plan.id
            self._audit("atualizou_plano_alimentar", plan_id, "Plano alimentar atualizado.")

        self._clear_form()
        self._reload_plan_table()

    def _build_plan(self) -> MealPlan:
        start_date = parse_date(self.start_date.text())
        end_date = self._optional_date(self.end_date.text())
        totals = self.service.calculate_totals(self.meals)
        self._show_totals(*totals)
        return MealPlan(
            id=self.selected_plan_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            start_date=start_date,
            end_date=end_date,
            objective=self.objective.text().strip(),
            target_energy_kcal=self._optional_float(self.target_energy.text(), "Meta kcal"),
            target_protein_g=self._optional_float(self.target_protein.text(), "Meta proteina"),
            target_carbohydrate_g=self._optional_float(
                self.target_carbohydrate.text(),
                "Meta carboidrato",
            ),
            target_fat_g=self._optional_float(self.target_fat.text(), "Meta lipidios"),
            total_energy_kcal=totals[0],
            total_protein_g=totals[1],
            total_carbohydrate_g=totals[2],
            total_fat_g=totals[3],
            notes=self.notes.toPlainText().strip(),
            meals=list(self.meals),
        )

    def _delete_plan(self) -> None:
        if self.selected_plan_id is None:
            QMessageBox.warning(self, "Plano alimentar", "Selecione um plano para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir plano alimentar",
            "Deseja excluir este plano? Refeicoes e itens serao preservados por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        plan_id = self.selected_plan_id
        self.repository.soft_delete(plan_id)
        self._audit("excluiu_plano_alimentar", plan_id, "Plano removido por exclusao logica.")
        self._clear_form()
        self._reload_plan_table()

    def _add_meal(self) -> None:
        meal = Meal(
            name=self.meal_name.text().strip(),
            time=self.meal_time.text().strip(),
            notes=self.meal_notes.text().strip(),
        )
        try:
            if not meal.name:
                self.service.validate_meal(meal)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return
        self.meals.append(meal)
        self.selected_meal_index = len(self.meals) - 1
        self._reload_meal_table()

    def _add_item(self) -> None:
        if self.selected_meal_index is None:
            QMessageBox.warning(self, "Plano alimentar", "Selecione ou adicione uma refeicao.")
            return

        try:
            item = MealPlanItem(
                food=self.food.text().strip(),
                quantity=self._required_float(self.quantity.text(), "Quantidade"),
                unit=self.unit.text().strip(),
                energy_kcal=self._optional_float(self.energy.text(), "Kcal") or 0,
                protein_g=self._optional_float(self.protein.text(), "Proteina") or 0,
                carbohydrate_g=self._optional_float(self.carbohydrate.text(), "Carboidrato") or 0,
                fat_g=self._optional_float(self.fat.text(), "Lipidios") or 0,
                substitutions=self.substitutions.text().strip(),
            )
            self.service.validate_item(item)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        meal = self.meals[self.selected_meal_index]
        self.meals[self.selected_meal_index] = Meal(
            name=meal.name,
            time=meal.time,
            notes=meal.notes,
            items=[*meal.items, item],
        )
        self._clear_item_fields()
        self._reload_meal_table()
        self._calculate_totals()

    def _remove_meal(self) -> None:
        if self.selected_meal_index is None:
            QMessageBox.warning(self, "Plano alimentar", "Selecione uma refeicao para remover.")
            return
        self.meals.pop(self.selected_meal_index)
        self.selected_meal_index = None
        self._reload_meal_table()
        self._calculate_totals()

    def _calculate_totals(self) -> None:
        try:
            totals = self.service.calculate_totals(self.meals)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return
        self._show_totals(*totals)
        self.shopping_list.setPlainText(self.service.build_shopping_list(self.meals))

    def _clear_form(self) -> None:
        self.selected_plan_id = None
        self.selected_meal_index = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        for field in [
            self.start_date,
            self.end_date,
            self.objective,
            self.target_energy,
            self.target_protein,
            self.target_carbohydrate,
            self.target_fat,
            self.total_energy,
            self.total_protein,
            self.total_carbohydrate,
            self.total_fat,
            self.meal_name,
            self.meal_time,
            self.meal_notes,
        ]:
            field.clear()
        self.notes.clear()
        self.meals = []
        self._clear_item_fields()
        self.shopping_list.clear()
        self._reload_meal_table()

    def _clear_item_fields(self) -> None:
        for field in [
            self.food,
            self.quantity,
            self.unit,
            self.energy,
            self.protein,
            self.carbohydrate,
            self.fat,
            self.substitutions,
        ]:
            field.clear()

    def _reload_patients(self) -> None:
        current_patient_id = None
        if self.patient.currentIndex() >= 0 and self.patient_ids_by_index:
            current_patient_id = self.patient_ids_by_index[self.patient.currentIndex()]

        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is None:
                continue
            self.patient.addItem(patient.name)
            self.patient_ids_by_index.append(patient.id)
        if current_patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_patient_id))
        self.patient.blockSignals(False)
        self._reload_appointments()

    def _reload_appointments(self) -> None:
        self.appointment.clear()
        self.appointment.addItem("Sem consulta vinculada")
        self.appointment_ids_by_index = [None]
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            return

        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        for appointment in self.appointment_repository.list_by_period():
            if appointment.patient_id != patient_id or appointment.id is None:
                continue
            self.appointment.addItem(
                f"{format_datetime(appointment.scheduled_at)} - {appointment.kind.value}"
            )
            self.appointment_ids_by_index.append(appointment.id)

    def _reload_meal_table(self) -> None:
        self.meal_table.setRowCount(len(self.meals))
        for row, meal in enumerate(self.meals):
            energy, protein, carbohydrate, _fat = self.service.calculate_totals([meal])
            self.meal_table.setItem(row, 0, QTableWidgetItem(meal.name))
            self.meal_table.setItem(row, 1, QTableWidgetItem(meal.time))
            self.meal_table.setItem(row, 2, QTableWidgetItem(str(len(meal.items))))
            self.meal_table.setItem(row, 3, QTableWidgetItem(f"{energy:.0f}"))
            self.meal_table.setItem(row, 4, QTableWidgetItem(f"{protein:.1f}"))
            self.meal_table.setItem(row, 5, QTableWidgetItem(f"{carbohydrate:.1f}"))
        self._refresh_meal_cards()

    def _reload_plan_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.plan_table.setRowCount(len(records))
        for row, record in enumerate(records):
            full = self.repository.get(record.id or 0)
            meals_count = len(full.meals) if full is not None else 0
            self.plan_table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.plan_table.setItem(row, 1, QTableWidgetItem(record.patient_name))
            self.plan_table.setItem(row, 2, QTableWidgetItem(format_date(record.start_date)))
            self.plan_table.setItem(row, 3, QTableWidgetItem(record.objective))
            self.plan_table.setItem(row, 4, QTableWidgetItem(f"{record.total_energy_kcal:.0f}"))
            self.plan_table.setItem(row, 5, QTableWidgetItem(f"{record.total_protein_g:.1f}"))
            self.plan_table.setItem(row, 6, QTableWidgetItem(str(meals_count)))

    def _save_smart_plan(self) -> None:
        if self.smart_patient.currentIndex() < 0:
            QMessageBox.warning(self, "Plano inteligente", "Cadastre um paciente antes do plano.")
            return

        try:
            values = {
                key: field.text().strip()
                for key, field in self.smart_inputs.items()
            }
            notes = self.smart_notes.toPlainText().strip()
            result = self.smart_definition.evaluator(
                self.smart_profile.currentText(),
                values,
                notes,
            )
            record = AdvancedClinicalRecord(
                module=self.smart_definition.module,
                patient_id=self.smart_patient_ids_by_index[self.smart_patient.currentIndex()],
                record_date=parse_date(self.smart_record_date.text()),
                profile=self.smart_profile.currentText(),
                inputs=values,
                result=result,
                notes=notes,
            )
        except (ValueError, IndexError) as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        record_id = self.smart_repository.add(record)
        self.audit_repository.log(
            user_id=self.current_user_id,
            action="registrou_plano_inteligente",
            entity="registros_clinicos_avancados",
            entity_id=record_id,
            details=f"Plano inteligente: {result}",
        )
        self.smart_result.setPlainText(result)
        self._reload_smart_table()
        QMessageBox.information(self, "Plano inteligente", "Plano inteligente registrado.")

    def _reload_smart_patients(self) -> None:
        current_patient_id = None
        if self.smart_patient.currentIndex() >= 0 and self.smart_patient_ids_by_index:
            current_patient_id = self.smart_patient_ids_by_index[
                self.smart_patient.currentIndex()
            ]

        self.smart_patient.blockSignals(True)
        self.smart_patient.clear()
        self.smart_patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is None:
                continue
            self.smart_patient.addItem(patient.name)
            self.smart_patient_ids_by_index.append(patient.id)
        if current_patient_id in self.smart_patient_ids_by_index:
            self.smart_patient.setCurrentIndex(
                self.smart_patient_ids_by_index.index(current_patient_id)
            )
        self.smart_patient.blockSignals(False)

    def _reload_smart_table(self) -> None:
        records = self.smart_repository.list_by_module(self.smart_definition.module)
        self.smart_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.smart_table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.smart_table.setItem(row, 1, QTableWidgetItem(format_date(record.record_date)))
            self.smart_table.setItem(row, 2, QTableWidgetItem(record.patient_name))
            self.smart_table.setItem(row, 3, QTableWidgetItem(record.profile))
            self.smart_table.setItem(row, 4, QTableWidgetItem(record.result))
            self.smart_table.setItem(row, 5, QTableWidgetItem(record.notes))

    def _clear_smart_plan(self) -> None:
        if self.smart_patient.count() > 0:
            self.smart_patient.setCurrentIndex(0)
        if self.smart_profile.count() > 0:
            self.smart_profile.setCurrentIndex(0)
        self.smart_record_date.setText(today_text())
        for field in self.smart_inputs.values():
            field.clear()
        self.smart_notes.clear()
        self.smart_result.clear()

    def _select_meal_from_table(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self.meals):
            return
        self.selected_meal_index = row
        meal = self.meals[row]
        self.meal_name.setText(meal.name)
        self.meal_time.setText(meal.time)
        self.meal_notes.setText(meal.notes)

    def _select_plan_from_table(self, row: int, _column: int) -> None:
        item = self.plan_table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Plano alimentar", "Plano nao encontrado.")
            self._reload_plan_table()
            return

        self.selected_plan_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.start_date.setText(format_date(record.start_date))
        self.end_date.setText(format_date(record.end_date))
        self.objective.setText(record.objective)
        self.target_energy.setText(self._format_optional(record.target_energy_kcal))
        self.target_protein.setText(self._format_optional(record.target_protein_g))
        self.target_carbohydrate.setText(self._format_optional(record.target_carbohydrate_g))
        self.target_fat.setText(self._format_optional(record.target_fat_g))
        self.notes.setPlainText(record.notes)
        self.meals = list(record.meals)
        self.selected_meal_index = None
        self._reload_meal_table()
        self._calculate_totals()

    def _show_totals(self, energy: float, protein: float, carbohydrate: float, fat: float) -> None:
        self.total_energy.setText(f"{energy:.0f}")
        self.total_protein.setText(f"{protein:.1f}")
        self.total_carbohydrate.setText(f"{carbohydrate:.1f}")
        self.total_fat.setText(f"{fat:.1f}")

    def _required_float(self, value: str, label: str) -> float:
        parsed = self._optional_float(value, label)
        if parsed is None or parsed <= 0:
            raise ValueError(f"{label} deve ser maior que zero.")
        return parsed

    def _optional_float(self, value: str, label: str) -> float | None:
        if not value.strip():
            return None
        try:
            parsed = float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc
        if parsed < 0:
            raise ValueError(f"{label} nao pode ser negativo.")
        return parsed

    def _optional_date(self, value: str) -> date | None:
        return parse_optional_date(value)

    def _format_optional(self, value: float | None) -> str:
        return "" if value is None else f"{value:g}"

    def _audit(self, action: str, plan_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="planos_alimentares",
            entity_id=plan_id,
            details=details,
        )
