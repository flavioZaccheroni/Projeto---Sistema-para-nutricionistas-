import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.laboratory_exam import LaboratoryExam, LaboratoryExamItem
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.dashboard_repository import DashboardRepository
from nutri_app.repositories.laboratory_exam_repository import LaboratoryExamRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.laboratory_exam import LaboratoryExamService


class LaboratoryExamServiceTest(unittest.TestCase):
    def test_monta_referencia_e_classifica_alerta(self) -> None:
        service = LaboratoryExamService()

        self.assertEqual(service.build_reference(70, 99), "70 - 99")
        self.assertEqual(service.classify_alert(120, 70, 99), "acima da referencia")
        self.assertEqual(service.classify_alert(60, 70, 99), "abaixo da referencia")
        self.assertEqual(service.classify_alert(85, 70, 99), "")

    def test_rejeita_nome_vazio(self) -> None:
        with self.assertRaises(ValueError):
            LaboratoryExamService().validate_item_name("")


class LaboratoryExamRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_exclui_e_alimenta_dashboard(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Exames", birth_date=date(1985, 6, 15))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 10, 11, 0),
                    kind=AppointmentKind.FOLLOW_UP,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = LaboratoryExamRepository(factory)

            exam_id = repository.add(
                LaboratoryExam(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    exam_date=date(2026, 7, 10),
                    laboratory="Lab Clinico",
                    notes="Rotina",
                    items=[
                        LaboratoryExamItem(
                            name="Glicemia",
                            value=130,
                            unit="mg/dL",
                            reference="70 - 99",
                            alert="acima da referencia",
                        ),
                        LaboratoryExamItem(
                            name="Creatinina",
                            value=0.9,
                            unit="mg/dL",
                            reference="0.6 - 1.2",
                        ),
                    ],
                )
            )
            listed = repository.list_active("exames")
            loaded = repository.get(exam_id)
            summary = DashboardRepository(factory).summary(today=date(2026, 7, 10))
            alerts = DashboardRepository(factory).recent_alerts()
            repository.update(
                LaboratoryExam(
                    id=exam_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    exam_date=date(2026, 7, 11),
                    laboratory="Lab Atualizado",
                    notes="Reteste",
                    items=[
                        LaboratoryExamItem(
                            name="Glicemia",
                            value=92,
                            unit="mg/dL",
                            reference="70 - 99",
                        )
                    ],
                )
            )
            updated = repository.get(exam_id)
            repository.soft_delete(exam_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Exames")
        self.assertEqual(len(loaded.items), 2)
        self.assertEqual(summary.critical_alerts, 1)
        self.assertEqual(alerts[0].source, "Exames")
        self.assertEqual(updated.laboratory, "Lab Atualizado")
        self.assertEqual(len(updated.items), 1)
        self.assertEqual(updated.items[0].alert, "")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
