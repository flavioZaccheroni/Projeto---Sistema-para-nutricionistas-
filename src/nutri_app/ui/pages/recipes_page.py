from __future__ import annotations

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

from nutri_app.domain.recipe import Recipe, RecipeIngredient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.recipe_repository import RecipeRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.recipe import RecipeService
from nutri_app.ui.pages.base import Page


class RecipesPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Receitas", "Ingredientes, preparo, rendimento e calculo nutricional.")
        self.repository = RecipeRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = RecipeService()
        self.selected_recipe_id: int | None = None
        self.selected_ingredient_index: int | None = None
        self.ingredients: list[RecipeIngredient] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar por nome ou categoria")
        self.search.textChanged.connect(self._reload_recipe_table)
        self.name = QLineEdit()
        self.category = QLineEdit()
        self.servings = QLineEdit()
        self.total_weight = QLineEdit()
        self.photo_path = QLineEdit()
        self.total_energy = QLineEdit()
        self.total_energy.setReadOnly(True)
        self.total_protein = QLineEdit()
        self.total_protein.setReadOnly(True)
        self.total_carbohydrate = QLineEdit()
        self.total_carbohydrate.setReadOnly(True)
        self.total_fat = QLineEdit()
        self.total_fat.setReadOnly(True)
        self.per_serving = QLineEdit()
        self.per_serving.setReadOnly(True)
        self.per_100g = QLineEdit()
        self.per_100g.setReadOnly(True)
        self.preparation = QTextEdit()
        self.preparation.setFixedHeight(70)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(55)

        self.ingredient_name = QLineEdit()
        self.ingredient_quantity = QLineEdit()
        self.ingredient_unit = QLineEdit()
        self.ingredient_weight = QLineEdit()
        self.ingredient_energy = QLineEdit()
        self.ingredient_protein = QLineEdit()
        self.ingredient_carbohydrate = QLineEdit()
        self.ingredient_fat = QLineEdit()
        self.ingredient_fiber = QLineEdit()
        self.ingredient_sodium = QLineEdit()
        self.ingredient_notes = QLineEdit()

        recipe_form = QFormLayout()
        recipe_form.addRow("Pesquisar", self.search)
        recipe_form.addRow("Nome", self.name)
        recipe_form.addRow("Categoria", self.category)
        recipe_form.addRow("Rendimento porcoes", self.servings)
        recipe_form.addRow("Peso total (g)", self.total_weight)
        recipe_form.addRow("Foto/caminho", self.photo_path)
        recipe_form.addRow("Energia total", self.total_energy)
        recipe_form.addRow("Proteina total", self.total_protein)
        recipe_form.addRow("Carboidrato total", self.total_carbohydrate)
        recipe_form.addRow("Lipidios total", self.total_fat)
        recipe_form.addRow("Por porcao", self.per_serving)
        recipe_form.addRow("Por 100g", self.per_100g)
        recipe_form.addRow("Modo de preparo", self.preparation)
        recipe_form.addRow("Observacoes", self.notes)

        ingredient_form = QFormLayout()
        ingredient_form.addRow("Ingrediente", self.ingredient_name)
        ingredient_form.addRow("Quantidade", self.ingredient_quantity)
        ingredient_form.addRow("Unidade", self.ingredient_unit)
        ingredient_form.addRow("Peso (g)", self.ingredient_weight)
        ingredient_form.addRow("Kcal", self.ingredient_energy)
        ingredient_form.addRow("Proteina (g)", self.ingredient_protein)
        ingredient_form.addRow("Carboidrato (g)", self.ingredient_carbohydrate)
        ingredient_form.addRow("Lipidios (g)", self.ingredient_fat)
        ingredient_form.addRow("Fibras (g)", self.ingredient_fiber)
        ingredient_form.addRow("Sodio (mg)", self.ingredient_sodium)
        ingredient_form.addRow("Obs. ingrediente", self.ingredient_notes)

        add_ingredient = QPushButton("Adicionar ingrediente")
        add_ingredient.clicked.connect(self._add_or_update_ingredient)
        clear_ingredient = QPushButton("Limpar ingrediente")
        clear_ingredient.clicked.connect(self._clear_ingredient_form)
        remove_ingredient = QPushButton("Remover ingrediente")
        remove_ingredient.clicked.connect(self._remove_ingredient)
        calculate = QPushButton("Calcular")
        calculate.clicked.connect(self._calculate)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_recipe)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_recipe)

        actions = QHBoxLayout()
        for button in [
            add_ingredient,
            clear_ingredient,
            remove_ingredient,
            calculate,
            save,
            new,
            delete,
        ]:
            actions.addWidget(button)
        actions.addStretch()

        self.ingredient_table = QTableWidget(0, 6)
        self.ingredient_table.setHorizontalHeaderLabels(
            ["Ingrediente", "Qtd", "Un", "Peso", "Kcal", "Proteina"]
        )
        self.ingredient_table.cellClicked.connect(self._select_ingredient_from_table)

        self.recipe_table = QTableWidget(0, 7)
        self.recipe_table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Categoria", "Porcoes", "Peso", "Kcal", "Ingredientes"]
        )
        self.recipe_table.cellClicked.connect(self._select_recipe_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(recipe_form)
        wrapper_layout.addRow(ingredient_form)
        wrapper_layout.addRow(actions)
        wrapper_layout.addRow(self.ingredient_table)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.recipe_table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_recipe_table()

    def _save_recipe(self) -> None:
        try:
            recipe = self._build_recipe()
            self.service.validate_recipe(recipe)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if recipe.id is None:
            recipe_id = self.repository.add(recipe)
            self._audit("criou_receita", recipe_id, "Receita criada.")
        else:
            self.repository.update(recipe)
            recipe_id = recipe.id
            self._audit("atualizou_receita", recipe_id, "Receita atualizada.")

        self._clear_form()
        self._reload_recipe_table()

    def _build_recipe(self) -> Recipe:
        totals = self.service.calculate_totals(self.ingredients)
        recipe = Recipe(
            id=self.selected_recipe_id,
            name=self.name.text().strip(),
            category=self.category.text().strip(),
            servings=self._required_float(self.servings.text(), "Rendimento"),
            total_weight_g=self._required_float(self.total_weight.text(), "Peso total"),
            preparation_method=self.preparation.toPlainText().strip(),
            photo_path=self.photo_path.text().strip(),
            total_energy_kcal=totals.energy_kcal,
            total_protein_g=totals.protein_g,
            total_carbohydrate_g=totals.carbohydrate_g,
            total_fat_g=totals.fat_g,
            total_fiber_g=totals.fiber_g,
            total_sodium_mg=totals.sodium_mg,
            notes=self.notes.toPlainText().strip(),
            ingredients=list(self.ingredients),
        )
        self._show_results(recipe)
        return recipe

    def _delete_recipe(self) -> None:
        if self.selected_recipe_id is None:
            QMessageBox.warning(self, "Receitas", "Selecione uma receita para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir receita",
            "Deseja excluir esta receita? Ingredientes serao preservados por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        recipe_id = self.selected_recipe_id
        self.repository.soft_delete(recipe_id)
        self._audit("excluiu_receita", recipe_id, "Receita removida por exclusao logica.")
        self._clear_form()
        self._reload_recipe_table()

    def _add_or_update_ingredient(self) -> None:
        try:
            ingredient = self._build_ingredient()
            self.service.validate_ingredient(ingredient)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if self.selected_ingredient_index is None:
            self.ingredients.append(ingredient)
        else:
            self.ingredients[self.selected_ingredient_index] = ingredient
        self._clear_ingredient_form()
        self._reload_ingredient_table()
        self._calculate()

    def _build_ingredient(self) -> RecipeIngredient:
        return RecipeIngredient(
            name=self.ingredient_name.text().strip(),
            quantity=self._required_float(self.ingredient_quantity.text(), "Quantidade"),
            unit=self.ingredient_unit.text().strip(),
            weight_g=self._required_float(self.ingredient_weight.text(), "Peso"),
            energy_kcal=self._optional_float(self.ingredient_energy.text(), "Kcal") or 0,
            protein_g=self._optional_float(self.ingredient_protein.text(), "Proteina") or 0,
            carbohydrate_g=self._optional_float(
                self.ingredient_carbohydrate.text(),
                "Carboidrato",
            )
            or 0,
            fat_g=self._optional_float(self.ingredient_fat.text(), "Lipidios") or 0,
            fiber_g=self._optional_float(self.ingredient_fiber.text(), "Fibras") or 0,
            sodium_mg=self._optional_float(self.ingredient_sodium.text(), "Sodio") or 0,
            notes=self.ingredient_notes.text().strip(),
        )

    def _remove_ingredient(self) -> None:
        if self.selected_ingredient_index is None:
            QMessageBox.warning(self, "Receitas", "Selecione um ingrediente para remover.")
            return
        self.ingredients.pop(self.selected_ingredient_index)
        self._clear_ingredient_form()
        self._reload_ingredient_table()
        self._calculate()

    def _calculate(self) -> None:
        try:
            recipe = self._build_recipe()
            self.service.validate_recipe(recipe)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return
        self._show_results(recipe)

    def _clear_form(self) -> None:
        self.selected_recipe_id = None
        self.selected_ingredient_index = None
        for field in [
            self.name,
            self.category,
            self.servings,
            self.total_weight,
            self.photo_path,
            self.total_energy,
            self.total_protein,
            self.total_carbohydrate,
            self.total_fat,
            self.per_serving,
            self.per_100g,
        ]:
            field.clear()
        self.preparation.clear()
        self.notes.clear()
        self.ingredients = []
        self._clear_ingredient_form()
        self._reload_ingredient_table()

    def _clear_ingredient_form(self) -> None:
        self.selected_ingredient_index = None
        for field in [
            self.ingredient_name,
            self.ingredient_quantity,
            self.ingredient_unit,
            self.ingredient_weight,
            self.ingredient_energy,
            self.ingredient_protein,
            self.ingredient_carbohydrate,
            self.ingredient_fat,
            self.ingredient_fiber,
            self.ingredient_sodium,
            self.ingredient_notes,
        ]:
            field.clear()

    def _reload_ingredient_table(self) -> None:
        self.ingredient_table.setRowCount(len(self.ingredients))
        for row, ingredient in enumerate(self.ingredients):
            self.ingredient_table.setItem(row, 0, QTableWidgetItem(ingredient.name))
            self.ingredient_table.setItem(row, 1, QTableWidgetItem(f"{ingredient.quantity:g}"))
            self.ingredient_table.setItem(row, 2, QTableWidgetItem(ingredient.unit))
            self.ingredient_table.setItem(row, 3, QTableWidgetItem(f"{ingredient.weight_g:g}"))
            self.ingredient_table.setItem(row, 4, QTableWidgetItem(f"{ingredient.energy_kcal:.0f}"))
            self.ingredient_table.setItem(row, 5, QTableWidgetItem(f"{ingredient.protein_g:.1f}"))

    def _reload_recipe_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.recipe_table.setRowCount(len(records))
        for row, record in enumerate(records):
            full = self.repository.get(record.id or 0)
            ingredients_count = len(full.ingredients) if full is not None else 0
            self.recipe_table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.recipe_table.setItem(row, 1, QTableWidgetItem(record.name))
            self.recipe_table.setItem(row, 2, QTableWidgetItem(record.category))
            self.recipe_table.setItem(row, 3, QTableWidgetItem(f"{record.servings:g}"))
            self.recipe_table.setItem(row, 4, QTableWidgetItem(f"{record.total_weight_g:g}"))
            self.recipe_table.setItem(row, 5, QTableWidgetItem(f"{record.total_energy_kcal:.0f}"))
            self.recipe_table.setItem(row, 6, QTableWidgetItem(str(ingredients_count)))

    def _select_ingredient_from_table(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self.ingredients):
            return
        self.selected_ingredient_index = row
        ingredient = self.ingredients[row]
        self.ingredient_name.setText(ingredient.name)
        self.ingredient_quantity.setText(f"{ingredient.quantity:g}")
        self.ingredient_unit.setText(ingredient.unit)
        self.ingredient_weight.setText(f"{ingredient.weight_g:g}")
        self.ingredient_energy.setText(f"{ingredient.energy_kcal:g}")
        self.ingredient_protein.setText(f"{ingredient.protein_g:g}")
        self.ingredient_carbohydrate.setText(f"{ingredient.carbohydrate_g:g}")
        self.ingredient_fat.setText(f"{ingredient.fat_g:g}")
        self.ingredient_fiber.setText(f"{ingredient.fiber_g:g}")
        self.ingredient_sodium.setText(f"{ingredient.sodium_mg:g}")
        self.ingredient_notes.setText(ingredient.notes)

    def _select_recipe_from_table(self, row: int, _column: int) -> None:
        item = self.recipe_table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Receitas", "Receita nao encontrada.")
            self._reload_recipe_table()
            return

        self.selected_recipe_id = record.id
        self.name.setText(record.name)
        self.category.setText(record.category)
        self.servings.setText(f"{record.servings:g}")
        self.total_weight.setText(f"{record.total_weight_g:g}")
        self.photo_path.setText(record.photo_path)
        self.preparation.setPlainText(record.preparation_method)
        self.notes.setPlainText(record.notes)
        self.ingredients = list(record.ingredients)
        self._clear_ingredient_form()
        self._reload_ingredient_table()
        self._show_results(record)

    def _show_results(self, recipe: Recipe) -> None:
        self.total_energy.setText(f"{recipe.total_energy_kcal:.0f}")
        self.total_protein.setText(f"{recipe.total_protein_g:.1f}")
        self.total_carbohydrate.setText(f"{recipe.total_carbohydrate_g:.1f}")
        self.total_fat.setText(f"{recipe.total_fat_g:.1f}")
        try:
            serving = self.service.calculate_per_serving(recipe)
            per_100g = self.service.calculate_per_100g(recipe)
        except ValueError:
            return
        self.per_serving.setText(
            f"{serving.energy_kcal:.0f} kcal | P {serving.protein_g:.1f}g | "
            f"C {serving.carbohydrate_g:.1f}g | L {serving.fat_g:.1f}g"
        )
        self.per_100g.setText(
            f"{per_100g.energy_kcal:.0f} kcal | P {per_100g.protein_g:.1f}g | "
            f"C {per_100g.carbohydrate_g:.1f}g | L {per_100g.fat_g:.1f}g"
        )

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

    def _audit(self, action: str, recipe_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="receitas",
            entity_id=recipe_id,
            details=details,
        )
