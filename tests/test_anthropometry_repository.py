import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.anthropometry import Anthropometry
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.patient import Patient
from nutri_app.repositories.anthropometry_repository import AnthropometryRepository
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AnthropometryRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_antropometria(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Antropometria", birth_date=date(1990, 1, 1))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 7, 8, 30),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = AnthropometryRepository(factory)

            anthropometry_id = repository.add(
                Anthropometry(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    assessment_date=date(2026, 7, 7),
                    weight_kg=70,
                    height_m=1.75,
                    bmi=22.86,
                    bmi_classification="eutrofia",
                    waist_cm=80,
                    hip_cm=100,
                    waist_hip_ratio=0.8,
                    waist_height_ratio=0.46,
                    notes="Avaliacao inicial",
                )
            )
            listed = repository.list_active("antropometria")
            repository.update(
                Anthropometry(
                    id=anthropometry_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    assessment_date=date(2026, 7, 8),
                    weight_kg=69,
                    height_m=1.75,
                    bmi=22.53,
                    bmi_classification="eutrofia",
                    waist_cm=79,
                    hip_cm=99,
                    waist_hip_ratio=0.8,
                    waist_height_ratio=0.45,
                    notes="Atualizado",
                )
            )
            updated = repository.get(anthropometry_id)
            repository.soft_delete(anthropometry_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Antropometria")
        self.assertIn("Consulta inicial", listed[0].appointment_label)
        self.assertEqual(updated.weight_kg, 69)
        self.assertEqual(updated.notes, "Atualizado")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
