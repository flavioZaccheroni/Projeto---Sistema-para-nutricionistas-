import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QCompleter

from nutri_app.ui.searchable_combo import make_searchable_combo


class SearchableComboTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_combo_e_editavel_e_nao_permite_inserir_texto_novo(self) -> None:
        combo = make_searchable_combo()

        self.assertTrue(combo.isEditable())
        self.assertEqual(combo.insertPolicy(), QComboBox.InsertPolicy.NoInsert)

    def test_completer_filtra_por_qualquer_trecho_do_nome(self) -> None:
        combo = make_searchable_combo()

        completer = combo.completer()

        self.assertIsNotNone(completer)
        self.assertEqual(completer.filterMode(), Qt.MatchFlag.MatchContains)
        self.assertEqual(completer.caseSensitivity(), Qt.CaseSensitivity.CaseInsensitive)
        self.assertEqual(completer.completionMode(), QCompleter.CompletionMode.PopupCompletion)

    def test_mantem_comportamento_de_selecao_por_indice(self) -> None:
        combo = make_searchable_combo()
        combo.addItem("Micheli Zaccheroni")
        combo.addItem("Flavio Henrique")

        combo.setCurrentIndex(1)

        self.assertEqual(combo.currentIndex(), 1)
        self.assertEqual(combo.currentText(), "Flavio Henrique")


if __name__ == "__main__":
    unittest.main()
