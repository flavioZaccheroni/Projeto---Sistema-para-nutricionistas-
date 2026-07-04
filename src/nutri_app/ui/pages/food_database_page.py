from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
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

from nutri_app.domain.food import Food, FoodSource
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.food import FoodService
from nutri_app.ui.pages.base import Page


class FoodDatabasePage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Banco de Alimentos", "TACO, TBCA, regionais e industrializados.")
        self.repository = FoodRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = FoodService()
        self.selected_food_id: int | None = None

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar por nome, categoria ou fonte")
        self.search.textChanged.connect(self._reload_table)
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.source = QComboBox()
        self.source.addItems([source.value for source in FoodSource])
        self.base_portion = QLineEdit("100")
        self.household_measure = QLineEdit()
        self.energy = QLineEdit()
        self.protein = QLineEdit()
        self.carbohydrate = QLineEdit()
        self.fat = QLineEdit()
        self.fiber = QLineEdit()
        self.sodium = QLineEdit()
        self.glycemic_index = QLineEdit()
        self.portion_to_calculate = QLineEdit("100")
        self.portion_result = QLineEdit()
        self.portion_result.setReadOnly(True)
        self.micronutrients = QTextEdit()
        self.micronutrients.setFixedHeight(60)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Nome", self.name)
        form.addRow("Categoria", self.category)
        form.addRow("Fonte", self.source)
        form.addRow("Porcao base (g)", self.base_portion)
        form.addRow("Medida caseira", self.household_measure)
        form.addRow("Energia (kcal)", self.energy)
        form.addRow("Proteina (g)", self.protein)
        form.addRow("Carboidrato (g)", self.carbohydrate)
        form.addRow("Lipidios (g)", self.fat)
        form.addRow("Fibras (g)", self.fiber)
        form.addRow("Sodio (mg)", self.sodium)
        form.addRow("Indice glicemico", self.glycemic_index)
        form.addRow("Porcao para calculo (g)", self.portion_to_calculate)
        form.addRow("Resultado por porcao", self.portion_result)
        form.addRow("Micronutrientes", self.micronutrients)
        form.addRow("Observacoes", self.notes)

        calculate = QPushButton("Calcular porcao")
        calculate.clicked.connect(self._calculate_portion)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_food)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_food)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Categoria", "Fonte", "Porcao", "Kcal", "Proteina", "Carboidrato"]
        )
        self.table.cellClicked.connect(self._select_food_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_table()

    def _save_food(self) -> None:
        try:
            food = self._build_food()
            self.service.validate(food)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if food.id is None:
            food_id = self.repository.add(food)
            self._audit("criou_alimento", food_id, "Alimento criado.")
        else:
            self.repository.update(food)
            food_id = food.id
            self._audit("atualizou_alimento", food_id, "Alimento atualizado.")

        self._clear_form()
        self._reload_table()

    def _build_food(self) -> Food:
        return Food(
            id=self.selected_food_id,
            name=self.name.text().strip(),
            category=self.category.text().strip(),
            source=FoodSource(self.source.currentText()),
            base_portion_g=self._required_float(self.base_portion.text(), "Porcao base"),
            household_measure=self.household_measure.text().strip(),
            energy_kcal=self._optional_float(self.energy.text(), "Energia") or 0,
            protein_g=self._optional_float(self.protein.text(), "Proteina") or 0,
            carbohydrate_g=self._optional_float(self.carbohydrate.text(), "Carboidrato") or 0,
            fat_g=self._optional_float(self.fat.text(), "Lipidios") or 0,
            fiber_g=self._optional_float(self.fiber.text(), "Fibras") or 0,
            sodium_mg=self._optional_float(self.sodium.text(), "Sodio") or 0,
            glycemic_index=self._optional_float(self.glycemic_index.text(), "Indice glicemico"),
            micronutrients=self.micronutrients.toPlainText().strip(),
            notes=self.notes.toPlainText().strip(),
        )

    def _calculate_portion(self) -> None:
        try:
            food = self._build_food()
            portion = self._required_float(self.portion_to_calculate.text(), "Porcao para calculo")
            nutrients = self.service.calculate_portion(food, portion)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        self.portion_result.setText(
            f"{nutrients.energy_kcal:.0f} kcal | "
            f"P {nutrients.protein_g:.1f}g | "
            f"C {nutrients.carbohydrate_g:.1f}g | "
            f"L {nutrients.fat_g:.1f}g"
        )

    def _delete_food(self) -> None:
        if self.selected_food_id is None:
            QMessageBox.warning(self, "Banco de alimentos", "Selecione um alimento para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir alimento",
            "Deseja excluir este alimento? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        food_id = self.selected_food_id
        self.repository.soft_delete(food_id)
        self._audit("excluiu_alimento", food_id, "Alimento removido por exclusao logica.")
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_food_id = None
        self.source.setCurrentIndex(0)
        self.base_portion.setText("100")
        self.portion_to_calculate.setText("100")
        for field in [
            self.name,
            self.category,
            self.household_measure,
            self.energy,
            self.protein,
            self.carbohydrate,
            self.fat,
            self.fiber,
            self.sodium,
            self.glycemic_index,
            self.portion_result,
        ]:
            field.clear()
        self.micronutrients.clear()
        self.notes.clear()

    def _reload_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.name))
            self.table.setItem(row, 2, QTableWidgetItem(record.category))
            self.table.setItem(row, 3, QTableWidgetItem(record.source.value))
            self.table.setItem(row, 4, QTableWidgetItem(f"{record.base_portion_g:g} g"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{record.energy_kcal:.0f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{record.protein_g:.1f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{record.carbohydrate_g:.1f}"))

    def _select_food_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Banco de alimentos", "Alimento nao encontrado.")
            self._reload_table()
            return

        self.selected_food_id = record.id
        self.name.setText(record.name)
        self.category.setText(record.category)
        self.source.setCurrentText(record.source.value)
        self.base_portion.setText(f"{record.base_portion_g:g}")
        self.household_measure.setText(record.household_measure)
        self.energy.setText(f"{record.energy_kcal:g}")
        self.protein.setText(f"{record.protein_g:g}")
        self.carbohydrate.setText(f"{record.carbohydrate_g:g}")
        self.fat.setText(f"{record.fat_g:g}")
        self.fiber.setText(f"{record.fiber_g:g}")
        self.sodium.setText(f"{record.sodium_mg:g}")
        self.glycemic_index.setText(
            "" if record.glycemic_index is None else f"{record.glycemic_index:g}"
        )
        self.micronutrients.setPlainText(record.micronutrients)
        self.notes.setPlainText(record.notes)
        self.portion_result.clear()

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

    def _audit(self, action: str, food_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="alimentos",
            entity_id=food_id,
            details=details,
        )
