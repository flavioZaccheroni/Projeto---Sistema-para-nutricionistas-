from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter

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
