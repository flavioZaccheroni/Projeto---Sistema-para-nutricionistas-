import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.ai_assistant import AIAssistantExecution, AIAssistantRequestType
from nutri_app.domain.patient import Patient
from nutri_app.repositories.ai_assistant_repository import AIAssistantRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.ai_assistant import AIAssistantService


class AIAssistantServiceTest(unittest.TestCase):
    def test_gera_alertas_inteligentes_com_contexto_clinico(self) -> None:
        service = AIAssistantService()

        result = service.generate(
            AIAssistantRequestType.SMART_ALERTS,
            {"bmi": 17.9, "lab_alerts": 2, "average_adherence": 45},
        )

        self.assertIn("IMC abaixo", result.result)
        self.assertIn("alerta(s) laboratorial", result.result)
        self.assertEqual(len(result.alerts), 3)

    def test_gera_sugestoes_alimentares_com_disclaimer(self) -> None:
        result = AIAssistantService().generate(
            AIAssistantRequestType.FOOD_SUGGESTIONS,
            {"meal_plan_objective": "Perda de peso"},
            "Paciente relata fome noturna",
        )

        self.assertIn("Revisao e decisao final", result.result)
        self.assertIn("saciedade", result.result)
        self.assertIn("fome noturna", result.result)


class AIAssistantRepositoryTest(unittest.TestCase):
    def test_monta_contexto_e_salva_execucao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente IA", birth_date=date(1987, 4, 3))
            )
            self._seed_context(factory, patient_id)
            repository = AIAssistantRepository(factory)

            context = repository.build_context(patient_id)
            execution_id = repository.add_execution(
                AIAssistantExecution(
                    patient_id=patient_id,
                    request_type=AIAssistantRequestType.CONSULTATION_SUMMARY,
                    input_text="Resumo",
                    result="Resultado gerado",
                    alerts="Alerta",
                )
            )
            records = repository.list_executions("ia")

        self.assertEqual(execution_id, 1)
        self.assertEqual(context["patient_name"], "Paciente IA")
        self.assertEqual(context["bmi"], 17.8)
        self.assertEqual(context["diagnosis"], "Risco nutricional")
        self.assertEqual(context["lab_alerts"], 1)
        self.assertEqual(context["average_adherence"], 50)
        self.assertEqual(records[0].result, "Resultado gerado")

    def _seed_context(self, factory: SQLiteConnectionFactory, patient_id: int) -> None:
        with factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO antropometrias (
                    paciente_id, data_avaliacao, peso_kg, altura_m, imc, classificacao_imc
                )
                VALUES (?, '2026-07-04', 50, 1.67, 17.8, 'Baixo peso')
                """,
                (patient_id,),
            )
            connection.execute(
                """
                INSERT INTO diagnosticos_nutricionais (
                    paciente_id, data_diagnostico, protocolo, criterios,
                    classificacao, gravidade, confirmado
                )
                VALUES (?, '2026-07-04', 'GLIM', 'Baixo peso', 'Risco nutricional', 'Moderada', 1)
                """,
                (patient_id,),
            )
            exam = connection.execute(
                """
                INSERT INTO exames_laboratoriais (paciente_id, data_exame)
                VALUES (?, '2026-07-04')
                """,
                (patient_id,),
            )
            connection.execute(
                """
                INSERT INTO exame_itens (exame_id, nome, valor, alerta)
                VALUES (?, 'Albumina', 3.0, 'Abaixo da referencia')
                """,
                (int(exam.lastrowid),),
            )
            connection.execute(
                """
                INSERT INTO planos_alimentares (
                    paciente_id, data_inicio, objetivo, energia_total_kcal,
                    proteina_total_g, carboidrato_total_g, lipidios_total_g
                )
                VALUES (?, '2026-07-04', 'Ganho ponderal', 2000, 90, 250, 60)
                """,
                (patient_id,),
            )
            connection.execute(
                """
                INSERT INTO paciente_app_adesoes (
                    paciente_id, data_registro, percentual_adesao
                )
                VALUES (?, '2026-07-05', 50)
                """,
                (patient_id,),
            )


if __name__ == "__main__":
    unittest.main()
