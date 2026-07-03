import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.repositories.dashboard_repository import DashboardRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class DashboardRepositoryTest(unittest.TestCase):
    def test_monta_indicadores_e_alertas_com_dados_reais(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            migrations = root / "migrations"
            migrations.mkdir()
            for migration in Path("database/migrations").glob("*.sql"):
                (migrations / migration.name).write_text(
                    migration.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            factory = SQLiteConnectionFactory(root / "test.sqlite")
            DatabaseMigrator(factory, migrations).migrate()
            with factory.connect() as connection:
                patient_id = connection.execute(
                    """
                    INSERT INTO pacientes (nome, data_nascimento, telefone)
                    VALUES ('Paciente Teste', '1990-01-01', '11999990000')
                    """
                ).lastrowid
                connection.execute(
                    """
                    INSERT INTO consultas (paciente_id, data_hora, tipo, status)
                    VALUES (?, ?, 'Consulta inicial', 'agendada')
                    """,
                    (patient_id, f"{date.today().isoformat()} 09:00"),
                )
                connection.execute(
                    """
                    INSERT INTO antropometrias (
                        paciente_id, data_avaliacao, peso_kg, altura_m, imc, classificacao_imc
                    )
                    VALUES (?, ?, 45, 1.70, 15.6, 'baixo peso')
                    """,
                    (patient_id, date.today().isoformat()),
                )

            repository = DashboardRepository(factory)
            summary = repository.summary(today=date.today())
            alerts = repository.recent_alerts()
            appointments = repository.upcoming_appointments()

        self.assertEqual(summary.active_patients, 1)
        self.assertEqual(summary.today_appointments, 1)
        self.assertEqual(summary.critical_alerts, 1)
        self.assertEqual(summary.pending_items, 1)
        self.assertEqual(alerts[0].patient_name, "Paciente Teste")
        self.assertEqual(appointments[0].kind, "Consulta inicial")


if __name__ == "__main__":
    unittest.main()
