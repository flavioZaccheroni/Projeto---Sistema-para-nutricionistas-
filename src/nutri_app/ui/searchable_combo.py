from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter


def make_searchable_combo() -> QComboBox:
    """Combo editavel com autocompletar que filtra por qualquer trecho do
    texto (nao so pelo inicio), para agilizar a selecao de paciente em
    clinicas com muitos cadastros.
    """
    combo = QComboBox()
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

    completer = combo.completer()
    if completer is not None:
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    return combo
