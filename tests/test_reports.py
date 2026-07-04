import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.domain.report import ClinicalReport
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.report_repository import ClinicalReportRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.report import ClinicalReportOptions, ClinicalReportService


class ClinicalReportServiceTest(unittest.TestCase):
    def test_gera_conteudo_clinico_e_exporta_txt(self) -> None:
        service = ClinicalReportService()
        patient = Patient(
            id=1,
            name="Paciente Relatorio",
            birth_date=date(1990, 1, 1),
            phone="11999990000",
            clinical_notes="Alergia relatada",
        )
        report = service.build(
            patient,
            ClinicalReportOptions(notes="Retorno em 30 dias."),
            {
                "anthropometry": {
                    "data_avaliacao": "2026-07-04",
                    "peso_kg": 70,
                    "altura_m": 1.7,
                    "imc": 24.2,
                    "classificacao_imc": "Eutrofia",
                },
                "diagnosis": {
                    "classificacao": "Sem risco",
                    "gravidade": "Leve",
                    "criterios": "Avaliacao clinica",
                    "conduta": "Acompanhamento",
                },
            },
        )
        with TemporaryDirectory() as tmp:
            path = service.export_text(report, Path(tmp), patient.name)
            content = path.read_text(encoding="utf-8")

        self.assertIn("Relatorio clinico - Paciente Relatorio", report.content)
        self.assertIn("Antropometria", report.content)
        self.assertIn("Retorno em 30 dias.", report.content)
        self.assertTrue(path.name.endswith("_paciente_relatorio_relatorio_clinico.txt"))
        self.assertEqual(content, report.content)

    def test_rejeita_relatorio_sem_secao(self) -> None:
        patient = Patient(id=1, name="Paciente", birth_date=date(1990, 1, 1))
        options = ClinicalReportOptions(
            include_anamnesis=False,
            include_anthropometry=False,
            include_laboratory_exams=False,
            include_diagnosis=False,
            include_meal_plan=False,
            include_energy_expenditure=False,
        )

        with self.assertRaises(ValueError):
            ClinicalReportService().build(patient, options, {})


class ClinicalReportRepositoryTest(unittest.TestCase):
    def test_salva_lista_e_monta_contexto_clinico(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Contexto", birth_date=date(1988, 5, 10))
            )
            self._seed_clinical_data(factory, patient_id)
            repository = ClinicalReportRepository(factory)
            context = repository.build_clinical_context(patient_id)
            report_id = repository.add(
                ClinicalReport(
                    patient_id=patient_id,
                    report_type="Clinico simples",
                    title="Relatorio teste",
                    file_path="exports/relatorios/teste.txt",
                    parameters="{}",
                    content="Conteudo",
                )
            )
            listed = repository.list_active("contexto")
            loaded = repository.get(report_id)

        self.assertEqual(context["anthropometry"]["imc"], 24.2)
        self.assertEqual(context["laboratory_exam"]["itens"][0]["nome"], "Glicemia")
        self.assertEqual(context["meal_plan"]["refeicoes"][0]["itens"][0]["alimento"], "Arroz")
        self.assertEqual(len(listed), 1)
        self.assertEqual(loaded.title, "Relatorio teste")
        self.assertEqual(loaded.content, "Conteudo")

    def _seed_clinical_data(self, factory: SQLiteConnectionFactory, patient_id: int) -> None:
        with factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO antropometrias (
                    paciente_id, data_avaliacao, peso_kg, altura_m, imc, classificacao_imc
                )
                VALUES (?, '2026-07-04', 70, 1.7, 24.2, 'Eutrofia')
                """,
                (patient_id,),
            )
            cursor = connection.execute(
                """
                INSERT INTO exames_laboratoriais (paciente_id, data_exame, laboratorio)
                VALUES (?, '2026-07-04', 'Lab')
                """,
                (patient_id,),
            )
            exam_id = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO exame_itens (exame_id, nome, valor, unidade, alerta)
                VALUES (?, 'Glicemia', 91, 'mg/dL', '')
                """,
                (exam_id,),
            )
            cursor = connection.execute(
                """
                INSERT INTO planos_alimentares (
                    paciente_id, data_inicio, objetivo, energia_total_kcal,
                    proteina_total_g, carboidrato_total_g, lipidios_total_g
                )
                VALUES (?, '2026-07-04', 'Manutencao', 1800, 90, 220, 60)
                """,
                (patient_id,),
            )
            plan_id = int(cursor.lastrowid)
            cursor = connection.execute(
                """
                INSERT INTO plano_refeicoes (plano_id, nome, horario)
                VALUES (?, 'Almoco', '12:00')
                """,
                (plan_id,),
            )
            meal_id = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO plano_itens (refeicao_id, alimento, quantidade, unidade)
                VALUES (?, 'Arroz', 120, 'g')
                """,
                (meal_id,),
            )


if __name__ == "__main__":
    unittest.main()
