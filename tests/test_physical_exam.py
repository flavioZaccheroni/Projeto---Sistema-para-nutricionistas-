import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.domain.physical_exam import NutritionPhysicalExam
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.physical_exam_repository import PhysicalExamRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PhysicalExamRepositoryTest(unittest.TestCase):
    def test_registra_achados_e_compara_com_avaliacao_anterior(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(Patient("Paciente", date(1960, 1, 1)))
            repository = PhysicalExamRepository(factory)
            repository.add(
                NutritionPhysicalExam(
                    patient_id=patient_id,
                    assessment_date=date(2026, 8, 10),
                    findings={"edema": "Moderado", "musculo_temporal": "Grave"},
                    summary="Edema e perda muscular importantes.",
                    severity="Grave",
                )
            )
            current_id = repository.add(
                NutritionPhysicalExam(
                    patient_id=patient_id,
                    assessment_date=date(2026, 8, 15),
                    findings={"edema": "Leve", "musculo_temporal": "Moderado"},
                    summary="Melhora parcial dos achados.",
                    severity="Moderada",
                )
            )

            changes = repository.compare_to_previous(current_id)
            history = repository.list_for_patient(patient_id)

        self.assertEqual(len(history), 2)
        self.assertTrue(any("edema: Moderado -> Leve" in change for change in changes))
        self.assertTrue(any("gravidade: Grave -> Moderada" in change for change in changes))

    def test_imagem_exige_consentimento_e_estados_semanticos_validos(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(Patient("Paciente", date(1980, 1, 1)))
            repository = PhysicalExamRepository(factory)

            invalid_exams = [
                NutritionPhysicalExam(
                    patient_id,
                    date(2026, 8, 15),
                    {"edema": "Desconhecido"},
                    "Resumo",
                    "Leve",
                ),
                NutritionPhysicalExam(
                    patient_id,
                    date(2026, 8, 15),
                    {"edema": "Ausente"},
                    "Resumo",
                    "Leve",
                    image_path="imagem.jpg",
                ),
            ]
            for exam in invalid_exams:
                with self.subTest(exam=exam), self.assertRaises(ValueError):
                    repository.add(exam)


if __name__ == "__main__":
    unittest.main()
