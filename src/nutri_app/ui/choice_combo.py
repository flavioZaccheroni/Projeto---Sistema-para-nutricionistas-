from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter

if TYPE_CHECKING:
    from nutri_app.repositories.choice_history_repository import ChoiceHistoryRepository

FOOD_CATEGORIES = (
    "Acucares e doces",
    "Bebidas",
    "Carnes e ovos",
    "Cereais e tuberculos",
    "Frutas",
    "Gorduras e oleos",
    "Hortalicas",
    "Laticinios",
    "Leguminosas",
    "Outros",
)

MEASURE_UNITS = (
    "g",
    "kg",
    "mg",
    "mcg",
    "ml",
    "L",
    "UI",
    "unidade",
    "fatia",
    "porcao",
    "colher de sopa",
    "colher de sobremesa",
    "colher de cha",
    "colher de servir",
    "xicara",
    "copo",
    "concha",
    "capsula",
    "comprimido",
    "gotas",
    "sache",
    "scoop",
)

PAYMENT_METHODS = (
    "Dinheiro",
    "PIX",
    "Cartao de credito",
    "Cartao de debito",
    "Transferencia",
    "Boleto",
)


INSURANCE_SEEDS = ("Particular",)

MOOD_SEEDS = ("Otimo", "Bom", "Regular", "Ruim")

LAB_EXAM_NAMES = (
    "Glicemia de jejum",
    "Hemoglobina glicada",
    "Insulina de jejum",
    "Colesterol total",
    "HDL",
    "LDL",
    "VLDL",
    "Triglicerideos",
    "Hemoglobina",
    "Hematocrito",
    "Leucocitos",
    "Plaquetas",
    "Ferritina",
    "Ferro serico",
    "Vitamina D (25-OH)",
    "Vitamina B12",
    "Acido folico",
    "Zinco",
    "Magnesio",
    "Calcio",
    "Potassio",
    "Sodio",
    "Creatinina",
    "Ureia",
    "Acido urico",
    "TGO (AST)",
    "TGP (ALT)",
    "Gama GT",
    "TSH",
    "T4 livre",
    "PCR ultrassensivel",
    "Albumina",
    "Proteinas totais",
    "Homocisteina",
)

LAB_EXAM_UNITS = (
    "mg/dL",
    "g/dL",
    "ng/mL",
    "pg/mL",
    "ng/dL",
    "mcg/dL",
    "U/L",
    "UI/L",
    "mUI/L",
    "uUI/mL",
    "mmol/L",
    "mEq/L",
    "%",
    "/mm3",
)

RECIPE_CATEGORY_SEEDS = (
    "Cafe da manha",
    "Almoco",
    "Jantar",
    "Lanche",
    "Prato principal",
    "Acompanhamento",
    "Salada",
    "Sopa",
    "Sobremesa",
    "Bebida",
)


def merge_options(learned: Sequence[str], seeds: Sequence[str] = ()) -> list[str]:
    """Sugestoes ja usadas primeiro, depois as sementes; sem repetir (ignora caixa)."""
    merged: list[str] = []
    seen: set[str] = set()
    for value in [*learned, *seeds]:
        key = value.strip().lower()
        if key and key not in seen:
            seen.add(key)
            merged.append(value.strip())
    return merged


def refresh_choices(
    combo: TextChoiceComboBox,
    history: ChoiceHistoryRepository,
    source: str,
    seeds: Sequence[str] = (),
) -> None:
    combo.set_options(merge_options(history.values(source), seeds))


class TextChoiceComboBox(QComboBox):
    """Combo para campos de texto com opcoes conhecidas.

    Expoe text()/setText()/clear() como um QLineEdit, para que o codigo das
    telas (que le, grava e limpa o campo como texto) continue igual. Atencao:
    clear() aqui restaura o valor padrao e NAO remove as opcoes, ao contrario
    de QComboBox.clear().

    Valores antigos que nao estao na lista (dados ja gravados) sao preservados:
    em combos fechados viram uma opcao temporaria; em editaveis ficam no texto.
    """

    def __init__(
        self,
        options: Sequence[str],
        *,
        editable: bool = False,
        allow_blank: bool = False,
        default: str = "",
    ) -> None:
        super().__init__()
        self._default = default
        self._allow_blank = allow_blank
        if allow_blank:
            self.addItem("")
        self.addItems(list(options))
        self._base_count = self.count()

        if editable:
            self.setEditable(True)
            self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            completer = self.completer()
            if completer is not None:
                completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.setText(default)

    def text(self) -> str:
        return self.currentText().strip()

    def setText(self, value: str | None) -> None:
        value = (value or "").strip()
        self._drop_temporary_options()

        if not value:
            self._select_empty()
            return

        index = self.findText(value, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.setCurrentIndex(index)
        elif self.isEditable():
            self.setEditText(value)
        else:
            self.addItem(value)
            self.setCurrentIndex(self.count() - 1)

    def clear(self) -> None:
        self.setText(self._default)

    def set_options(self, options: Sequence[str]) -> None:
        """Troca as opcoes mantendo o texto atual (ex.: sugestoes aprendidas)."""
        current = self.text()
        self.blockSignals(True)
        super().clear()
        if self._allow_blank:
            self.addItem("")
        self.addItems(list(options))
        self._base_count = self.count()
        self.blockSignals(False)
        self.setText(current)

    def setPlaceholderText(self, text: str) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(text)
        else:
            super().setPlaceholderText(text)

    def setMaxLength(self, length: int) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setMaxLength(length)

    def _select_empty(self) -> None:
        if self._allow_blank:
            self.setCurrentIndex(0)
        elif self.isEditable():
            self.setEditText("")
        elif self.count() > 0:
            self.setCurrentIndex(0)

    def _drop_temporary_options(self) -> None:
        while self.count() > self._base_count:
            self.removeItem(self.count() - 1)
