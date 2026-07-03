import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AppointmentRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_status_e_exclui_consulta(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Agenda", birth_date=date(1991, 3, 5))
            )
            repository = AppointmentRepository(factory)

            appointment_id = repository.add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 3, 14, 30),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                    notes="Consulta de teste",
                )
            )
            listed = repository.list_by_period(start=date(2026, 7, 1), end=date(2026, 7, 31))
            repository.set_status(appointment_id, AppointmentStatus.CONFIRMED)
            confirmed = repository.get(appointment_id)
            repository.update(
                Appointment(
                    id=appointment_id,
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 4, 9, 0),
                    kind=AppointmentKind.FOLLOW_UP,
                    status=AppointmentStatus.CONFIRMED,
                    notes="Retorno reagendado",
                )
            )
            updated = repository.get(appointment_id)
            repository.soft_delete(appointment_id)
            after_delete = repository.list_by_period()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Agenda")
        self.assertEqual(confirmed.status, AppointmentStatus.CONFIRMED)
        self.assertEqual(updated.kind, AppointmentKind.FOLLOW_UP)
        self.assertEqual(updated.scheduled_at, datetime(2026, 7, 4, 9, 0))
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
