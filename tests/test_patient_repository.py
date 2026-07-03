from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientRepositoryTest(unittest.TestCase):
    def test_salva_e_lista_paciente_com_campos_completos(self) -> None:
        with TemporaryDirectory() as tmp:
            repository = self._repository(Path(tmp))

            patient_id = repository.add(
                Patient(
                    name="Maria Silva",
                    birth_date=date(1990, 5, 20),
                    phone="11999990000",
                    email="maria@example.com",
                    health_insurance="Particular",
                    document="12345678900",
                    responsible="Joao Silva",
                    clinical_notes="Paciente teste",
                )
            )

            patients = repository.list_active()

        self.assertEqual(patient_id, 1)
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].name, "Maria Silva")
        self.assertEqual(patients[0].birth_date, date(1990, 5, 20))
        self.assertEqual(patients[0].health_insurance, "Particular")
        self.assertEqual(patients[0].document, "12345678900")
        self.assertEqual(patients[0].responsible, "Joao Silva")

    def test_pesquisa_atualiza_e_exclui_paciente_logicamente(self) -> None:
        with TemporaryDirectory() as tmp:
            repository = self._repository(Path(tmp))
            patient_id = repository.add(
                Patient(
                    name="Ana Costa",
                    birth_date=date(1985, 1, 10),
                    phone="1133334444",
                    email="ana@example.com",
                    document="ABC123",
                )
            )

            found = repository.search("abc")
            repository.update(
                Patient(
                    id=patient_id,
                    name="Ana Costa Atualizada",
                    birth_date=date(1985, 1, 10),
                    phone="1155556666",
                    email="ana.costa@example.com",
                    health_insurance="Convenio X",
                    document="ABC123",
                    responsible="",
                    clinical_notes="Atualizado",
                )
            )
            updated = repository.get(patient_id)
            repository.soft_delete(patient_id)
            active_after_delete = repository.list_active()

        self.assertEqual(len(found), 1)
        self.assertEqual(updated.name, "Ana Costa Atualizada")
        self.assertEqual(updated.phone, "1155556666")
        self.assertEqual(active_after_delete, [])

    def _repository(self, root: Path) -> PatientRepository:
        factory = SQLiteConnectionFactory(root / "test.sqlite")
        initialize_database(factory)
        return PatientRepository(factory)


if __name__ == "__main__":
    unittest.main()
