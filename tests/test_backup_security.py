import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.backup import BackupStatus
from nutri_app.repositories.backup_repository import BackupRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.backup import BackupService


class BackupServiceTest(unittest.TestCase):
    def test_cria_e_verifica_backup_sqlite_com_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            database_path = root / "local.sqlite"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("CREATE TABLE teste (id INTEGER PRIMARY KEY, nome TEXT)")
                connection.execute("INSERT INTO teste (nome) VALUES ('ok')")
                connection.commit()
            finally:
                connection.close()

            service = BackupService()
            result = service.create_backup(database_path, root / "backups", "Teste")
            verification = service.verify_backup(
                Path(result.record.file_path),
                result.record.checksum_sha256,
            )

        self.assertEqual(result.record.status, BackupStatus.CREATED)
        self.assertGreater(result.record.size_bytes, 0)
        self.assertEqual(verification.record.status, BackupStatus.VERIFIED)
        self.assertEqual(verification.record.checksum_sha256, result.record.checksum_sha256)

    def test_rejeita_backup_quando_banco_nao_existe(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                BackupService().create_backup(
                    Path(tmp) / "inexistente.sqlite",
                    Path(tmp) / "backups",
                )


class BackupRepositoryTest(unittest.TestCase):
    def test_salva_lista_atualiza_status_e_conta_permissoes(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            service = BackupService()
            result = service.create_backup(factory.database_path, Path(tmp) / "backups")
            repository = BackupRepository(factory)
            backup_id = repository.add(result.record)
            listed = repository.list_active()
            permissions = repository.count_permissions()
            repository.update_status(backup_id, BackupStatus.VERIFIED, "Validado")
            updated = repository.get(backup_id)

        self.assertEqual(len(listed), 1)
        self.assertGreater(permissions, 0)
        self.assertEqual(updated.status, BackupStatus.VERIFIED)
        self.assertEqual(updated.notes, "Validado")

    def test_monta_checklist_de_seguranca(self) -> None:
        checklist = BackupService().security_checklist(active_users=2, total_permissions=10)

        self.assertIn("Usuarios ativos cadastrados: 2", checklist)
        self.assertTrue(any("checksum SHA-256" in item for item in checklist))


if __name__ == "__main__":
    unittest.main()
