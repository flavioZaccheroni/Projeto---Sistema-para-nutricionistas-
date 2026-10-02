from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QCompleter, QLineEdit

from nutri_app.domain.food import Food
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.services.food import FoodService, PortionNutrients


class FoodLookup:
    """Autocompletar de um campo de nome de alimento com o Banco de Alimentos.

    Guarda o alimento vinculado ao texto digitado; a tela decide o que preencher
    (unidade, quantidade, nutrientes) pelo callback on_picked.
    """

    def __init__(
        self,
        repository: FoodRepository,
        service: FoodService,
        name_field: QLineEdit,
        on_picked: Callable[[Food], None],
    ) -> None:
        self.repository = repository
        self.service = service
        self.name_field = name_field
        self.on_picked = on_picked
        self.selected: Food | None = None
        self._foods_by_name: dict[str, Food] = {}
        self._foods_by_id: dict[int, Food] = {}

        self._model = QStringListModel()
        completer = QCompleter(self._model)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.activated[str].connect(self._pick_by_name)
        name_field.setCompleter(completer)
        name_field.setPlaceholderText("Digite para buscar no Banco de Alimentos")
        name_field.textEdited.connect(self._on_text_edited)
        self._completer = completer

    def reload(self) -> None:
        foods = [food for food in self.repository.list_active() if food.id is not None]
        self._foods_by_name = {food.name.strip().lower(): food for food in foods}
        self._foods_by_id = {food.id: food for food in foods}
        self._model.setStringList([food.name for food in foods])
        if self.selected is not None:
            self.selected = self._foods_by_id.get(self.selected.id)

    def select_by_id(self, food_id: int | None) -> None:
        self.selected = self._foods_by_id.get(food_id) if food_id is not None else None

    def clear_selection(self) -> None:
        self.selected = None

    def nutrients_for(self, grams: float) -> PortionNutrients | None:
        if self.selected is None or grams <= 0:
            return None
        try:
            return self.service.calculate_portion(self.selected, grams)
        except ValueError:
            return None

    def _on_text_edited(self, text: str) -> None:
        food = self._foods_by_name.get(text.strip().lower())
        if food is None:
            self.selected = None
            return
        self._pick(food)

    def _pick_by_name(self, name: str) -> None:
        food = self._foods_by_name.get(name.strip().lower())
        if food is not None:
            self._pick(food)

    def _pick(self, food: Food) -> None:
        self.selected = food
        self.name_field.setText(food.name)
        self.on_picked(food)
