import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit

from nutri_app.database.schema import initialize_database
from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.repositories.advanced_clinical_repository import AdvancedClinicalRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.choice_history_repository import ChoiceHistoryRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.ui.choice_combo import (
    ANAMNESIS_BARRIER_SEEDS,
    ANAMNESIS_TRIGGER_SEEDS,
    CRITERIA_COUNTS,
    TextChoiceComboBox,
    append_choice,
)
from nutri_app.ui.pages.advanced_module_page import AdvancedModulePage
from nutri_app.ui.pages.nutrition_diagnosis_page import NutritionDiagnosisPage


class AppendChoiceTest(unittest.TestCase):
    def test_acrescenta_com_virgula(self) -> None:
        self.assertEqual(append_choice("Ansiedade", "Estresse"), "Ansiedade, Estresse")

    def test_nao_repete_ignorando_caixa(self) -> None:
        self.assertEqual(append_choice("Ansiedade", "ansiedade"), "Ansiedade")

    def test_vazio_vira_so_a_escolha(self) -> None:
        self.assertEqual(append_choice("", "Culpa"), "Culpa")
        self.assertEqual(append_choice("A,  , B", "C"), "A, B, C")


class MultiChoiceComboTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _combo(self) -> TextChoiceComboBox:
        combo = TextChoiceComboBox(("Ansiedade", "Estresse", "Culpa"), editable=True, multi=True)
        combo.setText("")
        return combo

    def _pick(self, combo: TextChoiceComboBox, index: int) -> None:
        # Qt troca o texto pelo item e emite activated; repete o que o usuario faz.
        combo.setEditText(combo.itemText(index))
        combo.activated.emit(index)

    def test_escolhas_sucessivas_se_acumulam(self) -> None:
        combo = self._combo()

        self._pick(combo, 0)
        combo.showPopup()
        combo.hidePopup()
        self._pick(combo, 1)

        self.assertEqual(combo.text(), "Ansiedade, Estresse")

    def test_escolher_o_mesmo_item_duas_vezes_nao_duplica(self) -> None:
        combo = self._combo()
        self._pick(combo, 0)
        combo.showPopup()
        combo.hidePopup()

        self._pick(combo, 0)

        self.assertEqual(combo.text(), "Ansiedade")

    def test_texto_digitado_a_mao_tambem_recebe_a_escolha(self) -> None:
        combo = self._combo()
        combo.lineEdit().setText("Insonia")
        combo.lineEdit().textEdited.emit("Insonia")

        combo.showPopup()
        combo.hidePopup()
        self._pick(combo, 2)

        self.assertEqual(combo.text(), "Insonia, Culpa")

    def test_carregar_um_registro_atualiza_a_base_do_acumulo(self) -> None:
        combo = self._combo()
        self._pick(combo, 0)
        combo.setText("Tristeza")

        combo.showPopup()
        combo.hidePopup()
        self._pick(combo, 1)

        self.assertEqual(combo.text(), "Tristeza, Estresse")

    def test_multi_exige_combo_editavel(self) -> None:
        with self.assertRaises(ValueError):
            TextChoiceComboBox(("A",), multi=True)


class JsonHistoryTest(unittest.TestCase):
    def _factory(self):
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        return factory

    def _record(self, module: str, **inputs: str) -> AdvancedClinicalRecord:
        return AdvancedClinicalRecord(
            module=module,
            record_date=date(2026, 1, 1),
            profile="Emagrecimento",
            inputs=inputs,
            result="r",
        )

    def test_divide_por_virgula_e_ordena_por_uso(self) -> None:
        factory = self._factory()
        repo = AdvancedClinicalRepository(factory)
        repo.add(self._record("Anamnese Avancada", emotional_triggers="Ansiedade, Estresse"))
        repo.add(self._record("Anamnese Avancada", emotional_triggers="ansiedade; Culpa"))
        repo.add(self._record("Anamnese Avancada", emotional_triggers=""))

        values = ChoiceHistoryRepository(factory).values("anamnesis_triggers")

        self.assertEqual(values[0], "Ansiedade")
        self.assertCountEqual(values, ["Ansiedade", "Estresse", "Culpa"])

    def test_ignora_outros_modulos(self) -> None:
        factory = self._factory()
        AdvancedClinicalRepository(factory).add(
            self._record("Pediatria", emotional_triggers="Nao deveria aparecer")
        )

        self.assertEqual(ChoiceHistoryRepository(factory).values("anamnesis_triggers"), [])


class AnamnesisAdvancedPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _page(self, module: str, seed: AdvancedClinicalRecord | None = None):
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        if seed is not None:
            AdvancedClinicalRepository(factory).add(seed)
        definition = AdvancedClinicalService().by_module(module)
        return AdvancedModulePage(definition, factory, AuditRepository(factory), 1)

    def test_quatro_campos_viram_escolha_multipla_com_sugestoes(self) -> None:
        page = self._page("Anamnese Avancada")

        for key in ("pattern", "emotional_triggers", "gi_symptoms", "barriers"):
            self.assertIsInstance(page.inputs[key], TextChoiceComboBox, key)
        self.assertEqual(
            [
                page.inputs["emotional_triggers"].itemText(i)
                for i in range(page.inputs["emotional_triggers"].count())
            ],
            list(ANAMNESIS_TRIGGER_SEEDS),
        )

    def test_historico_vem_antes_das_sugestoes_iniciais(self) -> None:
        seed = AdvancedClinicalRecord(
            module="Anamnese Avancada",
            record_date=date(2026, 1, 1),
            profile="Emagrecimento",
            inputs={"barriers": "Plantao noturno"},
            result="r",
        )
        page = self._page("Anamnese Avancada", seed)

        first = page.inputs["barriers"].itemText(0)
        self.assertEqual(first, "Plantao noturno")
        self.assertIn(ANAMNESIS_BARRIER_SEEDS[0], [
            page.inputs["barriers"].itemText(i) for i in range(page.inputs["barriers"].count())
        ])

    def test_outros_modulos_continuam_com_campo_de_texto(self) -> None:
        page = self._page("Pediatria")

        self.assertIs(type(page.inputs["weight"]), QLineEdit)

    def test_sugestoes_ativam_o_calculo_de_risco_comportamental(self) -> None:
        # As sugestoes usam as palavras que o avaliador procura (ansiedade,
        # estresse, culpa...); tres delas elevam o risco a "alto".
        service = AdvancedClinicalService()
        result = service.evaluate_advanced_anamnesis(
            "Emagrecimento",
            {
                "emotional_triggers": "Ansiedade, Estresse, Culpa",
                "barriers": "Delivery frequente",
                "motivation": "8",
            },
            "",
        )

        self.assertIn("Risco comportamental alto", result)
        for seed in ("Ansiedade", "Estresse", "Culpa", "Compulsao alimentar"):
            self.assertIn(seed, ANAMNESIS_TRIGGER_SEEDS)


class DiagnosisCountsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _page(self) -> NutritionDiagnosisPage:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        return NutritionDiagnosisPage(factory, AuditRepository(factory), current_user_id=1)

    def test_contagens_sao_listas_de_0_a_10_com_padrao_zero(self) -> None:
        page = self._page()

        for combo in (page.primary_count, page.secondary_count):
            self.assertEqual(combo.text(), "0")
            items = [combo.itemText(i) for i in range(combo.count())]
            self.assertEqual(items, list(CRITERIA_COUNTS))

    def test_valor_escolhido_e_lido_como_numero(self) -> None:
        page = self._page()

        page.primary_count.setText("2")

        self.assertEqual(page._required_int(page.primary_count.text(), "x"), 2)

    def test_novo_formulario_volta_a_zero(self) -> None:
        page = self._page()
        page.secondary_count.setText("3")

        page._clear_form()

        self.assertEqual(page.secondary_count.text(), "0")


if __name__ == "__main__":
    unittest.main()
