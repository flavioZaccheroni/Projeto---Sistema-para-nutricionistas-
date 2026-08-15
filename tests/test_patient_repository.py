import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

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
                    document="529.982.247-25",
                    cns="174598435280018",
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
        self.assertEqual(patients[0].document, "52998224725")
        self.assertEqual(patients[0].cns, "174598435280018")
        self.assertEqual(patients[0].medical_record_number, "NCP-000001")
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
                    document="52998224725",
                )
            )

            found = repository.search("529982")
            repository.update(
                Patient(
                    id=patient_id,
                    name="Ana Costa Atualizada",
                    birth_date=date(1985, 1, 10),
                    phone="1155556666",
                    email="ana.costa@example.com",
                    health_insurance="Convenio X",
                    document="52998224725",
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

    def test_impede_cpf_cns_e_prontuario_duplicados(self) -> None:
        with TemporaryDirectory() as tmp:
            repository = self._repository(Path(tmp))
            repository.add(
                Patient(
                    name="Primeiro Paciente",
                    birth_date=date(1990, 1, 1),
                    document="52998224725",
                    cns="174598435280018",
                    medical_record_number="HOSP-100",
                )
            )

            duplicates = [
                Patient("CPF duplicado", date(1991, 1, 1), document="529.982.247-25"),
                Patient("CNS duplicado", date(1992, 1, 1), cns="174598435280018"),
                Patient("Prontuario duplicado", date(1993, 1, 1), medical_record_number="hosp-100"),
            ]
            for patient in duplicates:
                with self.subTest(patient=patient.name), self.assertRaises(ValueError):
                    repository.add(patient)

    def test_rejeita_cpf_e_cns_invalidos(self) -> None:
        with TemporaryDirectory() as tmp:
            repository = self._repository(Path(tmp))
            with self.assertRaisesRegex(ValueError, "CPF invalido"):
                repository.add(Patient("CPF invalido", date(1990, 1, 1), document="11111111111"))
            with self.assertRaisesRegex(ValueError, "CNS invalido"):
                repository.add(Patient("CNS invalido", date(1990, 1, 1), cns="123456789012345"))

    def _repository(self, root: Path) -> PatientRepository:
        factory = SQLiteConnectionFactory(root / "test.sqlite")
        initialize_database(factory)
        return PatientRepository(factory)


if __name__ == "__main__":
    unittest.main()
