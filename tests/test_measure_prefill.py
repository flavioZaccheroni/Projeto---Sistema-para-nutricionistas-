import os
import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit

from nutri_app.database.schema import initialize_database
from nutri_app.domain.anthropometry import Anthropometry
from nutri_app.domain.patient import Patient
from nutri_app.repositories.anthropometry_repository import AnthropometryRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.services.measure_suggestion import age_in_months, suggest_measures
from nutri_app.ui.measure_prefill import MeasurePrefill
from nutri_app.ui.pages.advanced_module_page import AdvancedModulePage
from nutri_app.ui.pages.body_composition_page import BodyCompositionPage
from nutri_app.ui.pages.energy_expenditure_page import EnergyExpenditurePage

TODAY = date(2026, 10, 2)


def _record(patient_id: int, days_ago: int, weight: float = 70, height_m: float = 1.7):
    return Anthropometry(
        patient_id=patient_id,
        assessment_date=TODAY - timedelta(days=days_ago),
        weight_kg=weight,
        height_m=height_m,
        bmi=24.2,
        bmi_classification="Eutrofia",
        waist_cm=80,
        hip_cm=95,
    )


class SuggestMeasuresTest(unittest.TestCase):
    ADULT = date(1990, 1, 1)
    CHILD = date(2020, 1, 1)

    def test_sem_antropometria_sugere_so_a_idade(self) -> None:
        result = suggest_measures(self.ADULT, None, TODAY)

        self.assertEqual(result.age_years, 36)
        self.assertIsNone(result.weight_kg)
        self.assertIsNone(result.height_cm)

    def test_medida_recente_sugere_peso_altura_e_circunferencias(self) -> None:
        result = suggest_measures(self.ADULT, _record(1, 10), TODAY)

        self.assertEqual(result.weight_kg, 70)
        self.assertAlmostEqual(result.height_cm, 170)
        self.assertEqual(result.waist_cm, 80)
        self.assertEqual(result.source_date, TODAY - timedelta(days=10))

    def test_adulto_com_medida_antiga_mantem_so_a_altura(self) -> None:
        result = suggest_measures(self.ADULT, _record(1, 400), TODAY)

        self.assertIsNone(result.weight_kg)
        self.assertIsNone(result.waist_cm)
        self.assertAlmostEqual(result.height_cm, 170)

    def test_crianca_com_medida_antiga_nao_sugere_nada(self) -> None:
        result = suggest_measures(self.CHILD, _record(1, 400, 15, 1.0), TODAY)

        self.assertIsNone(result.weight_kg)
        self.assertIsNone(result.height_cm)
        self.assertIsNone(result.source_date)

    def test_limite_de_90_dias(self) -> None:
        self.assertEqual(suggest_measures(self.ADULT, _record(1, 90), TODAY).weight_kg, 70)
        self.assertIsNone(suggest_measures(self.ADULT, _record(1, 91), TODAY).weight_kg)

    def test_medida_com_data_futura_e_ignorada(self) -> None:
        result = suggest_measures(self.ADULT, _record(1, -5), TODAY)

        self.assertIsNone(result.weight_kg)
        self.assertIsNone(result.height_cm)

    def test_idade_em_meses(self) -> None:
        self.assertEqual(age_in_months(date(2025, 12, 15), date(2026, 10, 2)), 9)
        self.assertEqual(age_in_months(date(2025, 12, 1), date(2026, 10, 2)), 10)


class AnthropometryLatestTest(unittest.TestCase):
    def test_latest_ignora_registros_excluidos_e_pega_o_mais_recente(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "t.sqlite")
            initialize_database(factory)
            pid = PatientRepository(factory).add(Patient(name="A", birth_date=date(1990, 1, 1)))
            repo = AnthropometryRepository(factory)
            repo.add(_record(pid, 60, weight=80))
            newest = repo.add(_record(pid, 5, weight=75))
            removed = repo.add(_record(pid, 1, weight=99))
            repo.soft_delete(removed)

            latest = repo.latest_for_patient(pid)

            self.assertEqual(latest.id, newest)
            self.assertEqual(latest.weight_kg, 75)
            self.assertIsNone(repo.latest_for_patient(9999))


class MeasurePrefillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _setup(self):
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        patients = PatientRepository(factory)
        ana = patients.add(Patient(name="Ana", birth_date=date(2005, 1, 1)))
        bruno = patients.add(Patient(name="Bruno", birth_date=date(1950, 1, 1)))
        repo = AnthropometryRepository(factory)
        repo.add(
            Anthropometry(
                patient_id=ana,
                assessment_date=date.today() - timedelta(days=1),
                weight_kg=60,
                height_m=1.65,
                bmi=22,
                bmi_classification="Eutrofia",
            )
        )
        fields = {"age": QLineEdit(), "weight": QLineEdit(), "height": QLineEdit()}
        return MeasurePrefill(repo, fields), fields, patients.get(ana), patients.get(bruno)

    def test_preenche_e_troca_ao_mudar_de_paciente(self) -> None:
        prefill, fields, ana, bruno = self._setup()

        prefill.apply(ana)
        self.assertEqual(fields["weight"].text(), "60")
        self.assertEqual(fields["height"].text(), "165")

        prefill.apply(bruno)
        self.assertEqual(fields["age"].text(), str(bruno_age()))
        self.assertEqual(fields["weight"].text(), "")
        self.assertEqual(fields["height"].text(), "")

    def test_nao_sobrescreve_o_que_o_usuario_digitou(self) -> None:
        prefill, fields, ana, bruno = self._setup()
        prefill.apply(ana)
        fields["weight"].setText("62.5")

        prefill.apply(bruno)

        self.assertEqual(fields["weight"].text(), "62.5")

    def test_tooltip_informa_a_data_de_origem(self) -> None:
        prefill, fields, ana, _bruno = self._setup()

        prefill.apply(ana)

        self.assertIn("antropometria de", fields["weight"].toolTip())
        self.assertEqual(fields["age"].toolTip(), "")

    def test_sem_paciente_limpa_so_o_que_era_automatico(self) -> None:
        prefill, fields, ana, _bruno = self._setup()
        prefill.apply(ana)

        prefill.apply(None)

        self.assertEqual(fields["weight"].text(), "")
        self.assertEqual(fields["age"].text(), "")

    def test_rejeita_chave_desconhecida(self) -> None:
        with self.assertRaises(ValueError):
            MeasurePrefill(None, {"cor_do_cabelo": QLineEdit()})


def bruno_age() -> int:
    from nutri_app.domain.patient import calculate_age

    return calculate_age(date(1950, 1, 1))


class PagesPrefillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _factory(self):
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        return factory

    def test_gasto_energetico_troca_a_idade_ao_trocar_de_paciente(self) -> None:
        factory = self._factory()
        patients = PatientRepository(factory)
        patients.add(Patient(name="Ana Jovem", birth_date=date(2005, 1, 1)))
        patients.add(Patient(name="Bruno Idoso", birth_date=date(1950, 1, 1)))
        page = EnergyExpenditurePage(factory, AuditRepository(factory), current_user_id=1)

        page.patient.setCurrentIndex(0)
        young = page.age.text()
        page.patient.setCurrentIndex(1)

        self.assertNotEqual(page.age.text(), young)
        self.assertEqual(page.age.text(), str(bruno_age()))

    def test_gasto_energetico_traz_peso_e_altura_da_ultima_antropometria(self) -> None:
        factory = self._factory()
        pid = PatientRepository(factory).add(Patient(name="Ana", birth_date=date(1990, 1, 1)))
        AnthropometryRepository(factory).add(
            Anthropometry(
                patient_id=pid,
                assessment_date=date.today() - timedelta(days=3),
                weight_kg=68.5,
                height_m=1.72,
                bmi=23,
                bmi_classification="Eutrofia",
            )
        )

        page = EnergyExpenditurePage(factory, AuditRepository(factory), current_user_id=1)

        self.assertEqual(page.weight.text(), "68.5")
        self.assertEqual(page.height.text(), "172")

    def test_composicao_corporal_traz_o_peso(self) -> None:
        factory = self._factory()
        pid = PatientRepository(factory).add(Patient(name="Ana", birth_date=date(1990, 1, 1)))
        AnthropometryRepository(factory).add(
            Anthropometry(
                patient_id=pid,
                assessment_date=date.today(),
                weight_kg=71,
                height_m=1.7,
                bmi=24,
                bmi_classification="Eutrofia",
            )
        )

        page = BodyCompositionPage(factory, AuditRepository(factory), current_user_id=1)

        self.assertEqual(page.weight.text(), "71")

    def test_pediatria_traz_idade_em_meses_peso_e_altura(self) -> None:
        factory = self._factory()
        birth = date.today().replace(year=date.today().year - 2)
        pid = PatientRepository(factory).add(Patient(name="Crianca", birth_date=birth))
        AnthropometryRepository(factory).add(
            Anthropometry(
                patient_id=pid,
                assessment_date=date.today(),
                weight_kg=12.4,
                height_m=0.88,
                bmi=16,
                bmi_classification="Eutrofia",
            )
        )
        definition = AdvancedClinicalService().by_module("Pediatria")
        page = AdvancedModulePage(definition, factory, AuditRepository(factory), 1)

        page.patient.setCurrentIndex(page.patient_ids.index(pid))

        self.assertEqual(page.inputs["age_months"].text(), "24")
        self.assertEqual(page.inputs["weight"].text(), "12.4")
        self.assertEqual(page.inputs["height_cm"].text(), "88")

    def test_outros_modulos_avancados_nao_sao_preenchidos(self) -> None:
        factory = self._factory()
        PatientRepository(factory).add(Patient(name="Ana", birth_date=date(1990, 1, 1)))
        definition = AdvancedClinicalService().by_module("Nefrologia")
        page = AdvancedModulePage(definition, factory, AuditRepository(factory), 1)

        self.assertIsNone(page.measure_prefill)


if __name__ == "__main__":
    unittest.main()
