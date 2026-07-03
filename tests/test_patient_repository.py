from datetime import date
import unittest

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientRepositoryTest(unittest.TestCase):
    def test_salva_e_lista_paciente(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            repository = PatientRepository(factory)

            patient_id = repository.add(
                Patient(
                    name="Maria Silva",
                    birth_date=date(1990, 5, 20),
                    phone="11999990000",
                    email="maria@example.com",
                    clinical_notes="Paciente teste",
                )
            )

            patients = repository.list_active()

        self.assertEqual(patient_id, 1)
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].name, "Maria Silva")
        self.assertEqual(patients[0].birth_date, date(1990, 5, 20))


if __name__ == "__main__":
    unittest.main()
