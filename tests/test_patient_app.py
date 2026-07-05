import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.meal_plan import Meal, MealPlan
from nutri_app.domain.patient import Patient
from nutri_app.domain.patient_app import (
    PatientAppAccess,
    PatientAppAdherence,
    PatientAppPublication,
    PatientPublicationType,
)
from nutri_app.repositories.meal_plan_repository import MealPlanRepository
from nutri_app.repositories.patient_app_repository import PatientAppRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.patient_app import PatientAppService


class PatientAppServiceTest(unittest.TestCase):
    def test_gera_codigo_e_classifica_adesao(self) -> None:
        service = PatientAppService()

        code = service.generate_access_code()

        self.assertEqual(len(code), 8)
        self.assertTrue(code.isalnum())
        self.assertEqual(service.adherence_classification(90), "Alta adesao")
        self.assertEqual(service.adherence_classification(70), "Adesao parcial")
        self.assertEqual(service.adherence_classification(40), "Baixa adesao")

    def test_rejeita_publicacao_sem_conteudo(self) -> None:
        publication = PatientAppPublication(
            patient_id=1,
            publication_type=PatientPublicationType.GUIDANCE,
            title="Orientacao",
            content="",
        )

        with self.assertRaises(ValueError):
            PatientAppService().validate_publication(publication)

    def test_rejeita_adesao_fora_da_faixa(self) -> None:
        adherence = PatientAppAdherence(
            patient_id=1,
            record_date=date(2026, 7, 4),
            adherence_percent=120,
        )

        with self.assertRaises(ValueError):
            PatientAppService().validate_adherence(adherence)


class PatientAppRepositoryTest(unittest.TestCase):
    def test_salva_acesso_publicacao_adesao_e_resumo(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(
                    name="Paciente App",
                    birth_date=date(1995, 2, 12),
                    email="paciente@app.local",
                )
            )
            plan_id = MealPlanRepository(factory).add(
                MealPlan(
                    patient_id=patient_id,
                    start_date=date(2026, 7, 4),
                    objective="Educacao alimentar",
                    total_energy_kcal=1800,
                    meals=[Meal(name="Cafe da manha")],
                )
            )
            repository = PatientAppRepository(factory)

            access_id = repository.upsert_access(
                PatientAppAccess(
                    patient_id=patient_id,
                    email_login="paciente@app.local",
                    access_code="ABC12345",
                )
            )
            publication_id = repository.add_publication(
                PatientAppPublication(
                    patient_id=patient_id,
                    meal_plan_id=plan_id,
                    publication_type=PatientPublicationType.MEAL_PLAN,
                    title="Plano da semana",
                    content="Seguir refeicoes orientadas.",
                    publication_date=date(2026, 7, 4),
                )
            )
            adherence_id = repository.add_adherence(
                PatientAppAdherence(
                    patient_id=patient_id,
                    publication_id=publication_id,
                    record_date=date(2026, 7, 5),
                    adherence_percent=80,
                    mood="Bom",
                    difficulties="Sem dificuldades",
                )
            )
            accesses = repository.list_accesses("app")
            publications = repository.list_publications("app")
            adherences = repository.list_adherences("app")
            summary = repository.summary()

        self.assertEqual(access_id, 1)
        self.assertEqual(adherence_id, 1)
        self.assertEqual(accesses[0].patient_name, "Paciente App")
        self.assertEqual(publications[0].meal_plan_label, "2026-07-04 - Educacao alimentar")
        self.assertEqual(adherences[0].publication_title, "Plano da semana")
        self.assertEqual(summary.total_accesses, 1)
        self.assertEqual(summary.total_published, 1)
        self.assertEqual(summary.average_adherence, 80)

    def test_atualiza_acesso_existente_por_paciente(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Codigo", birth_date=date(1990, 1, 1))
            )
            repository = PatientAppRepository(factory)

            first_id = repository.upsert_access(
                PatientAppAccess(
                    patient_id=patient_id,
                    email_login="primeiro@app.local",
                    access_code="ABC12345",
                )
            )
            second_id = repository.upsert_access(
                PatientAppAccess(
                    patient_id=patient_id,
                    email_login="segundo@app.local",
                    access_code="XYZ98765",
                )
            )
            accesses = repository.list_accesses("codigo")

        self.assertEqual(first_id, second_id)
        self.assertEqual(len(accesses), 1)
        self.assertEqual(accesses[0].email_login, "segundo@app.local")
        self.assertEqual(accesses[0].access_code, "XYZ98765")


if __name__ == "__main__":
    unittest.main()
