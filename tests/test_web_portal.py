import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.finance import FinancialEntry, FinancialEntryType, FinancialStatus
from nutri_app.domain.patient import Patient
from nutri_app.domain.patient_app import (
    PatientAppPublication,
    PatientPublicationType,
)
from nutri_app.domain.web_portal import WebPortalPublishRecord
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.finance_repository import FinanceRepository
from nutri_app.repositories.patient_app_repository import PatientAppRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.web_portal_repository import WebPortalRepository
from nutri_app.services.web_portal import WebPortalService


class WebPortalServiceTest(unittest.TestCase):
    def test_publica_portal_estatico_com_paginas_html_e_css(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            repository = WebPortalRepository(factory)
            snapshot = repository.build_snapshot()
            output = Path(tmp) / "portal"

            total_pages = WebPortalService().publish_static_portal(snapshot, output)

            index = (output / "index.html").read_text(encoding="utf-8")
            css = (output / "assets" / "style.css").read_text(encoding="utf-8")

        self.assertEqual(total_pages, 3)
        self.assertIn("Nutri Clinic Pro", index)
        self.assertIn("Portal Web", index)
        self.assertIn(".card", css)


class WebPortalRepositoryTest(unittest.TestCase):
    def test_monta_snapshot_e_salva_historico_de_publicacao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Web", birth_date=date(1994, 6, 1))
            )
            AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 15, 10, 0),
                    kind=AppointmentKind.FOLLOW_UP,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            PatientAppRepository(factory).add_publication(
                PatientAppPublication(
                    patient_id=patient_id,
                    publication_type=PatientPublicationType.GUIDANCE,
                    title="Orientacao web",
                    content="Beber agua.",
                    publication_date=date(2026, 7, 5),
                )
            )
            FinanceRepository(factory).add(
                FinancialEntry(
                    patient_id=patient_id,
                    entry_type=FinancialEntryType.RECEIVABLE,
                    category="Consulta",
                    description="Consulta",
                    amount=200,
                    due_date=date(2026, 7, 20),
                    status=FinancialStatus.OPEN,
                )
            )
            repository = WebPortalRepository(factory)

            snapshot = repository.build_snapshot()
            record_id = repository.add_publish_record(
                WebPortalPublishRecord(
                    title="Portal teste",
                    output_path="exports/portal_web",
                    status="Gerado",
                    total_pages=3,
                )
            )
            records = repository.list_publish_records()

        self.assertEqual(record_id, 1)
        self.assertEqual(snapshot.cards[0].value, "1")
        self.assertEqual(snapshot.publications[0].title, "Orientacao web")
        self.assertEqual(snapshot.appointments[0].title, "Paciente Web")
        self.assertEqual(records[0].title, "Portal teste")


if __name__ == "__main__":
    unittest.main()
