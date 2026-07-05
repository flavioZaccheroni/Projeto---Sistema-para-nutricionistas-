import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.integration import (
    ExternalIntegration,
    IntegrationDirection,
    IntegrationExecution,
    IntegrationStatus,
    IntegrationType,
)
from nutri_app.domain.patient import Patient
from nutri_app.repositories.integration_repository import IntegrationRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.integration import IntegrationService


class IntegrationServiceTest(unittest.TestCase):
    def test_valida_endpoint_e_simula_sincronizacao(self) -> None:
        integration = ExternalIntegration(
            name="Laboratorio ABC",
            integration_type=IntegrationType.LABORATORY,
            endpoint="https://api.lab.local",
        )

        result = IntegrationService().simulate_sync(integration, "exames")

        self.assertIn("Laboratorio ABC", result)
        self.assertIn("exames", result)

    def test_rejeita_endpoint_invalido(self) -> None:
        integration = ExternalIntegration(
            name="API invalida",
            integration_type=IntegrationType.WEBHOOK,
            endpoint="ftp://servidor",
        )

        with self.assertRaises(ValueError):
            IntegrationService().validate_integration(integration)

    def test_parseia_payload_laboratorial(self) -> None:
        payload = """
        {
          "data_exame": "2026-07-04",
          "laboratorio": "Lab Integrado",
          "itens": [
            {"nome": "Glicemia", "valor": 92, "unidade": "mg/dL"}
          ]
        }
        """

        exam = IntegrationService().parse_laboratory_payload(payload, patient_id=1)

        self.assertEqual(exam.exam_date, date(2026, 7, 4))
        self.assertEqual(exam.laboratory, "Lab Integrado")
        self.assertEqual(exam.items[0].name, "Glicemia")
        self.assertEqual(exam.items[0].value, 92)


class IntegrationRepositoryTest(unittest.TestCase):
    def test_salva_integracao_e_execucao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            PatientRepository(factory).add(
                Patient(name="Paciente Integracao", birth_date=date(1990, 1, 1))
            )
            repository = IntegrationRepository(factory)

            integration_id = repository.add_integration(
                ExternalIntegration(
                    name="Webhook Clinica",
                    integration_type=IntegrationType.WEBHOOK,
                    endpoint="https://webhook.local",
                )
            )
            execution_id = repository.add_execution(
                IntegrationExecution(
                    integration_id=integration_id,
                    direction=IntegrationDirection.EXPORT,
                    entity="pacientes",
                    status=IntegrationStatus.SUCCESS,
                    payload="{}",
                    result="OK",
                )
            )
            integrations = repository.list_integrations()
            executions = repository.list_executions()

        self.assertEqual(integration_id, 1)
        self.assertEqual(execution_id, 1)
        self.assertEqual(integrations[0].name, "Webhook Clinica")
        self.assertEqual(executions[0].integration_name, "Webhook Clinica")
        self.assertEqual(executions[0].result, "OK")


if __name__ == "__main__":
    unittest.main()
