import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.nutrition_diagnosis import (
    DiagnosisProtocol,
    DiagnosisSeverity,
    NutritionDiagnosis,
)
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.nutrition_diagnosis_repository import NutritionDiagnosisRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.nutrition_diagnosis import NutritionDiagnosisService


class NutritionDiagnosisServiceTest(unittest.TestCase):
    def test_classifica_glim_positivo_com_criterios_fenotipico_e_etiologico(self) -> None:
        classification, severity = NutritionDiagnosisService().classify(
            DiagnosisProtocol.GLIM,
            primary_criteria=1,
            secondary_criteria=1,
            severe_marker=True,
        )

        self.assertEqual(classification, "desnutricao relacionada a doenca")
        self.assertEqual(severity, DiagnosisSeverity.SEVERE)

    def test_classifica_fragilidade_e_pre_fragilidade(self) -> None:
        service = NutritionDiagnosisService()

        self.assertEqual(
            service.classify(DiagnosisProtocol.FRAILTY, 2, 1)[0],
            "fragilidade",
        )
        self.assertEqual(
            service.classify(DiagnosisProtocol.FRAILTY, 1, 0)[0],
            "pre-fragilidade",
        )


class NutritionDiagnosisRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_diagnostico(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Diagnostico", birth_date=date(1975, 3, 5))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 11, 9, 0),
                    kind=AppointmentKind.FOLLOW_UP,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = NutritionDiagnosisRepository(factory)

            diagnosis_id = repository.add(
                NutritionDiagnosis(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    diagnosis_date=date(2026, 7, 11),
                    protocol=DiagnosisProtocol.GLIM,
                    criteria="fenotipico: 1; etiologico: 1",
                    classification="desnutricao relacionada a doenca",
                    severity=DiagnosisSeverity.MODERATE,
                    confirmed=False,
                    conduct="Acompanhar ingestao",
                    notes="Avaliacao inicial",
                )
            )
            listed = repository.list_active("diagnostico")
            repository.update(
                NutritionDiagnosis(
                    id=diagnosis_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    diagnosis_date=date(2026, 7, 12),
                    protocol=DiagnosisProtocol.BRASPEN,
                    criteria="criterios: 3",
                    classification="desnutricao",
                    severity=DiagnosisSeverity.SEVERE,
                    confirmed=True,
                    conduct="Plano de recuperacao nutricional",
                    notes="Confirmado",
                )
            )
            updated = repository.get(diagnosis_id)
            repository.soft_delete(diagnosis_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Diagnostico")
        self.assertIn("Retorno", listed[0].appointment_label)
        self.assertEqual(updated.protocol, DiagnosisProtocol.BRASPEN)
        self.assertEqual(updated.severity, DiagnosisSeverity.SEVERE)
        self.assertTrue(updated.confirmed)
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
