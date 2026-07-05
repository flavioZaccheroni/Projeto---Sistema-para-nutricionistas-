import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.finance import FinancialEntry, FinancialEntryType, FinancialStatus
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.finance_repository import FinanceRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.finance import FinanceService


class FinanceServiceTest(unittest.TestCase):
    def test_marca_recebimento_vencido_quando_passou_vencimento(self) -> None:
        entry = FinancialEntry(
            entry_type=FinancialEntryType.RECEIVABLE,
            category="Consulta",
            description="Consulta inicial",
            amount=250,
            due_date=date(2026, 7, 1),
        )

        status = FinanceService().normalize_status(entry, reference_date=date(2026, 7, 5))

        self.assertEqual(status, FinancialStatus.OVERDUE)

    def test_rejeita_valor_invalido(self) -> None:
        entry = FinancialEntry(
            entry_type=FinancialEntryType.PAYABLE,
            category="Despesa",
            description="Aluguel",
            amount=0,
            due_date=date(2026, 7, 10),
        )

        with self.assertRaises(ValueError):
            FinanceService().validate(entry)


class FinanceRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_resume_e_exclui_lancamento(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Financeiro", birth_date=date(1991, 3, 4))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 20, 9, 0),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = FinanceRepository(factory)

            receivable_id = repository.add(
                FinancialEntry(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    entry_type=FinancialEntryType.RECEIVABLE,
                    category="Consulta",
                    description="Consulta inicial",
                    amount=300,
                    due_date=date(2026, 7, 20),
                    payment_date=date(2026, 7, 20),
                    payment_method="Pix",
                    status=FinancialStatus.PAID,
                )
            )
            repository.add(
                FinancialEntry(
                    entry_type=FinancialEntryType.PAYABLE,
                    category="Operacional",
                    description="Material",
                    amount=80,
                    due_date=date(2026, 7, 25),
                    status=FinancialStatus.OPEN,
                )
            )
            listed = repository.list_active("financeiro")
            loaded = repository.get(receivable_id)
            summary = repository.monthly_summary(2026, 7)
            repository.update(
                FinancialEntry(
                    id=receivable_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    entry_type=FinancialEntryType.RECEIVABLE,
                    category="Consulta",
                    description="Consulta inicial ajustada",
                    amount=320,
                    due_date=date(2026, 7, 20),
                    payment_date=date(2026, 7, 20),
                    payment_method="Cartao",
                    status=FinancialStatus.PAID,
                )
            )
            updated = repository.get(receivable_id)
            repository.soft_delete(receivable_id)
            after_delete = repository.list_active("financeiro")

        self.assertEqual(len(listed), 1)
        self.assertEqual(loaded.patient_name, "Paciente Financeiro")
        self.assertEqual(summary.total_receivable, 300)
        self.assertEqual(summary.total_payable, 80)
        self.assertEqual(summary.total_received, 300)
        self.assertEqual(summary.open_balance, 220)
        self.assertEqual(updated.description, "Consulta inicial ajustada")
        self.assertEqual(updated.payment_method, "Cartao")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
