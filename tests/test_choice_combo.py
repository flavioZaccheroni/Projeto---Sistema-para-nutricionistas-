import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.ui.choice_combo import (
    FOOD_CATEGORIES,
    MEASURE_UNITS,
    PAYMENT_METHODS,
    TextChoiceComboBox,
)


class TextChoiceComboBoxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _items(self, combo: TextChoiceComboBox) -> list[str]:
        return [combo.itemText(index) for index in range(combo.count())]

    def test_com_opcao_em_branco_comeca_vazio(self) -> None:
        combo = TextChoiceComboBox(FOOD_CATEGORIES, allow_blank=True)

        self.assertEqual(combo.text(), "")
        self.assertEqual(self._items(combo)[0], "")
        self.assertEqual(self._items(combo)[1:], list(FOOD_CATEGORIES))

    def test_set_text_seleciona_opcao_existente_sem_diferenciar_caixa(self) -> None:
        combo = TextChoiceComboBox(FOOD_CATEGORIES, allow_blank=True)

        combo.setText("frutas")

        self.assertEqual(combo.text(), "Frutas")

    def test_valor_antigo_fora_da_lista_e_preservado_em_combo_fechado(self) -> None:
        combo = TextChoiceComboBox(FOOD_CATEGORIES, allow_blank=True)

        combo.setText("Regional")

        self.assertEqual(combo.text(), "Regional")

    def test_valor_temporario_some_ao_carregar_outro_registro(self) -> None:
        combo = TextChoiceComboBox(FOOD_CATEGORIES, allow_blank=True)
        combo.setText("Regional")

        combo.setText("Bebidas")

        self.assertEqual(combo.text(), "Bebidas")
        self.assertNotIn("Regional", self._items(combo))

    def test_clear_restaura_o_padrao_e_nao_remove_as_opcoes(self) -> None:
        combo = TextChoiceComboBox(PAYMENT_METHODS, allow_blank=True)
        combo.setText("PIX")

        combo.clear()

        self.assertEqual(combo.text(), "")
        self.assertEqual(self._items(combo), ["", *PAYMENT_METHODS])

    def test_combo_editavel_aceita_valor_fora_da_lista(self) -> None:
        combo = TextChoiceComboBox(MEASURE_UNITS, editable=True)

        combo.setText("pedaco")

        self.assertTrue(combo.isEditable())
        self.assertEqual(combo.text(), "pedaco")
        self.assertEqual(combo.count(), len(MEASURE_UNITS))

    def test_valor_padrao_e_aplicado_na_criacao_e_no_clear(self) -> None:
        combo = TextChoiceComboBox(MEASURE_UNITS, editable=True, default="ml")
        self.assertEqual(combo.text(), "ml")

        combo.setText("g")
        combo.clear()

        self.assertEqual(combo.text(), "ml")

    def test_set_text_none_ou_vazio_volta_ao_vazio(self) -> None:
        combo = TextChoiceComboBox(PAYMENT_METHODS, allow_blank=True)
        combo.setText("Boleto")

        combo.setText(None)

        self.assertEqual(combo.text(), "")


if __name__ == "__main__":
    unittest.main()
