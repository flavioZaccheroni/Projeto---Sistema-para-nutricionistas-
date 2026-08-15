import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.hospitalization import Hospitalization
from nutri_app.domain.patient import Patient
from nutri_app.repositories.hospitalization_repository import HospitalizationRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class HospitalizationRepositoryTest(unittest.TestCase):
    def test_registra_e_atualiza_episodio_de_internacao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient("Paciente Internado", date(1970, 5, 4), health_insurance="Convenio A")
            )
            repository = HospitalizationRepository(factory)

            hospitalization_id = repository.add(
                Hospitalization(
                    patient_id=patient_id,
                    admission_date=date(2026, 8, 10),
                    unit="Hospital Central",
                    ward="Clinica medica",
                    bed="12-B",
                    health_insurance="Convenio A",
                    responsible_team="Equipe Multiprofissional 1",
                    diagnoses="Desnutricao; pneumonia",
                )
            )
            active = repository.get(hospitalization_id)
            repository.update(
                Hospitalization(
                    id=hospitalization_id,
                    patient_id=patient_id,
                    admission_date=active.admission_date,
                    discharge_date=date(2026, 8, 15),
                    unit=active.unit,
                    ward=active.ward,
                    bed=active.bed,
                    health_insurance=active.health_insurance,
                    responsible_team=active.responsible_team,
                    diagnoses=active.diagnoses,
                    discharge_condition="Estavel, acompanhamento ambulatorial",
                    status="Alta",
                )
            )
            completed = repository.list_for_patient(patient_id)

        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].status, "Alta")
        self.assertEqual(completed[0].bed, "12-B")
        self.assertEqual(completed[0].discharge_date, date(2026, 8, 15))

    def test_valida_datas_status_e_unidade(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(Patient("Paciente", date(1980, 1, 1)))
            repository = HospitalizationRepository(factory)

            invalid_cases = [
                Hospitalization(patient_id, date(2026, 8, 10), ""),
                Hospitalization(patient_id, date(2026, 8, 10), "UTI", status="Alta"),
                Hospitalization(
                    patient_id,
                    date(2026, 8, 10),
                    "UTI",
                    discharge_date=date(2026, 8, 9),
                    status="Alta",
                ),
            ]
            for hospitalization in invalid_cases:
                with self.subTest(hospitalization=hospitalization), self.assertRaises(ValueError):
                    repository.add(hospitalization)


if __name__ == "__main__":
    unittest.main()
