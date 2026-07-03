import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.anamnesis import Anamnesis
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.patient import Patient
from nutri_app.repositories.anamnesis_repository import AnamnesisRepository
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AnamnesisRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_anamnese(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Anamnese", birth_date=date(1992, 8, 12))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 5, 10, 30),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = AnamnesisRepository(factory)

            anamnesis_id = repository.add(
                Anamnesis(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    chief_complaint="Perda de peso",
                    current_disease_history="Relata perda ponderal recente.",
                    pathological_history="Sem comorbidades.",
                    family_history="Historico familiar de diabetes.",
                    food_routine="Tres refeicoes ao dia.",
                    eating_behavior="Beliscos noturnos.",
                    gastrointestinal_symptoms="Nega sintomas.",
                    notes="Observacao inicial.",
                )
            )
            listed = repository.list_active("anamnese")
            repository.update(
                Anamnesis(
                    id=anamnesis_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    chief_complaint="Perda de peso e inapetencia",
                    current_disease_history="Atualizado.",
                )
            )
            updated = repository.get(anamnesis_id)
            repository.soft_delete(anamnesis_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Anamnese")
        self.assertIn("Consulta inicial", listed[0].appointment_label)
        self.assertEqual(updated.chief_complaint, "Perda de peso e inapetencia")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
