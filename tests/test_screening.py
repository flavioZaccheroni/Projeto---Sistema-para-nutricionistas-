import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.patient import Patient
from nutri_app.domain.screening import Screening, ScreeningProtocol
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.screening_repository import ScreeningRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.screening import ScreeningService


class ScreeningServiceTest(unittest.TestCase):
    def test_classifica_protocolos_principais(self) -> None:
        service = ScreeningService()

        self.assertEqual(service.classify(ScreeningProtocol.NRS_2002, 3), "risco nutricional")
        self.assertEqual(service.classify(ScreeningProtocol.MUST, 0), "baixo risco")
        self.assertEqual(service.classify(ScreeningProtocol.MUST, 2), "alto risco")
        self.assertEqual(service.classify(ScreeningProtocol.MST, 2), "risco nutricional")
        self.assertEqual(service.classify(ScreeningProtocol.MNA_SF, 7), "desnutricao")

    def test_rejeita_pontuacao_negativa(self) -> None:
        with self.assertRaises(ValueError):
            ScreeningService().classify(ScreeningProtocol.MUST, -1)


class ScreeningRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_triagem(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Triagem", birth_date=date(1993, 9, 9))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 6, 8, 0),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = ScreeningRepository(factory)

            screening_id = repository.add(
                Screening(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    protocol=ScreeningProtocol.NRS_2002,
                    score=3,
                    classification="risco nutricional",
                    notes="Triagem inicial",
                )
            )
            listed = repository.list_active("triagem")
            repository.update(
                Screening(
                    id=screening_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    protocol=ScreeningProtocol.MUST,
                    score=1,
                    classification="medio risco",
                    notes="Atualizada",
                )
            )
            updated = repository.get(screening_id)
            repository.soft_delete(screening_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Triagem")
        self.assertIn("Consulta inicial", listed[0].appointment_label)
        self.assertEqual(updated.protocol, ScreeningProtocol.MUST)
        self.assertEqual(updated.classification, "medio risco")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
