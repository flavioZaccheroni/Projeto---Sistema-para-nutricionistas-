from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.domain.meal_plan import MealPlan
from nutri_app.services.meal_plan_suggestion import MealPlanSuggestionService, SuggestedMealPlan
from nutri_app.ui.date_format import format_date, parse_date, today_text
from nutri_app.ui.input_masks import apply_date_mask
from nutri_app.ui.pages.meal_plan_page_widgets import configure_table


class SmartMealPlanTabMixin:
    def _build_smart_plan_tab(self) -> QWidget:
        self.smart_patient = QComboBox()
        self.smart_record_date = QLineEdit(today_text())
        apply_date_mask(self.smart_record_date)
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
        configure_table(self.smart_table)

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

    def _save_smart_plan(self) -> None:
        if self.smart_patient.currentIndex() < 0:
            QMessageBox.warning(self, "Plano inteligente", "Cadastre um paciente antes do plano.")
            return

        try:
            values = {key: field.text().strip() for key, field in self.smart_inputs.items()}
            notes = self.smart_notes.toPlainText().strip()
            profile = self.smart_profile.currentText()
            record_date = parse_date(self.smart_record_date.text())
            patient_id = self.smart_patient_ids_by_index[self.smart_patient.currentIndex()]
            energy = self._smart_float(values.get("energy"), "Energia")
            protein = self._smart_float(values.get("protein"), "Proteina")
            carbohydrate = self._smart_float(values.get("carbohydrate"), "Carboidrato")
            fat = self._smart_float(values.get("fat"), "Lipidios")
            meal_count = max(int(self._smart_float(values.get("meals"), "Refeicoes") or 6), 1)
            excluded_terms = [
                term.strip()
                for term in values.get("restrictions", "").replace(";", ",").split(",")
                if term.strip()
            ]
            patient_allergies = self.patient_allergy_repository.list_for_patient(patient_id)
            excluded_terms.extend(allergy.allergen for allergy in patient_allergies)

            foods = self.food_repository.list_active()
            suggestion = MealPlanSuggestionService().suggest(
                profile, energy, meal_count, excluded_terms, foods, self.food_service
            )
            meals = [meal for meal in suggestion.meals if meal.items]
            totals = self.service.calculate_totals(meals)

            plan = MealPlan(
                patient_id=patient_id,
                start_date=record_date,
                objective=f"Plano inteligente - {profile}",
                target_energy_kcal=energy or None,
                target_protein_g=protein or None,
                target_carbohydrate_g=carbohydrate or None,
                target_fat_g=fat or None,
                total_energy_kcal=totals[0],
                total_protein_g=totals[1],
                total_carbohydrate_g=totals[2],
                total_fat_g=totals[3],
                notes=notes,
                meals=meals,
            )
            self.service.validate_plan(plan)
        except (ValueError, IndexError) as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        plan_id = self.repository.add(plan)
        self._audit("criou_plano_alimentar", plan_id, "Plano criado pelo Plano Inteligente.")

        result = self._build_smart_summary(profile, plan, suggestion, plan_id)
        record = AdvancedClinicalRecord(
            module=self.smart_definition.module,
            patient_id=patient_id,
            record_date=record_date,
            profile=profile,
            inputs={**values, "plano_alimentar_id": str(plan_id)},
            result=result,
            notes=notes,
        )
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
        self._open_generated_plan(plan_id)
        QMessageBox.information(
            self,
            "Plano inteligente",
            "Plano inteligente gerado e salvo como plano alimentar. Revise na aba "
            "'Plano alimentar' antes de entregar ao paciente.",
        )

    def _build_smart_summary(
        self, profile: str, plan: MealPlan, suggestion: SuggestedMealPlan, plan_id: int
    ) -> str:
        lines = [
            f"Plano {profile}: {plan.total_energy_kcal:.0f} kcal, "
            f"P {plan.total_protein_g:.0f}g, C {plan.total_carbohydrate_g:.0f}g, "
            f"L {plan.total_fat_g:.0f}g em {len(plan.meals)} refeicoes "
            f"(plano alimentar #{plan_id}).",
        ]
        lines.extend(suggestion.substitution_notes)
        if suggestion.caution_note:
            lines.append(f"Atencao: {suggestion.caution_note}")
        return "\n".join(lines)

    def _open_generated_plan(self, plan_id: int) -> None:
        loaded = self.repository.get(plan_id)
        if loaded is None:
            return
        self.selected_plan_id = loaded.id
        if loaded.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(loaded.patient_id))
        self._reload_appointments()
        self.start_date.setText(format_date(loaded.start_date))
        self.objective.setText(loaded.objective)
        self.notes.setPlainText(loaded.notes)
        self.meals = list(loaded.meals)
        self.selected_meal_index = None
        self._reload_meal_table()
        self._calculate_totals()
        self._reload_plan_table()
        self.tabs.setCurrentIndex(0)

    def _smart_float(self, value: str | None, label: str) -> float:
        text = (value or "").strip()
        if not text:
            return 0.0
        try:
            return float(text.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc

    def _reload_smart_patients(self) -> None:
        current_patient_id = None
        if self.smart_patient.currentIndex() >= 0 and self.smart_patient_ids_by_index:
            current_patient_id = self.smart_patient_ids_by_index[self.smart_patient.currentIndex()]

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
