from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from nutri_app.domain.backup import BackupRecord, BackupStatus


@dataclass(frozen=True)
class BackupResult:
    record: BackupRecord
    message: str


class BackupService:
    def create_backup(
        self,
        database_path: Path,
        backup_dir: Path,
        note: str = "",
    ) -> BackupResult:
        if not database_path.exists():
            raise ValueError("Banco de dados local nao encontrado para backup.")

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"nutri_clinic_pro_{timestamp}.sqlite"
        source = sqlite3.connect(database_path)
        destination = sqlite3.connect(backup_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        record = BackupRecord(
            file_path=str(backup_path),
            size_bytes=backup_path.stat().st_size,
            checksum_sha256=self.calculate_checksum(backup_path),
            status=BackupStatus.CREATED,
            notes=note,
        )
        return BackupResult(record=record, message="Backup criado com sucesso.")

    def verify_backup(self, backup_path: Path, expected_checksum: str) -> BackupResult:
        if not backup_path.exists():
            raise ValueError("Arquivo de backup nao encontrado.")
        checksum = self.calculate_checksum(backup_path)
        status = BackupStatus.VERIFIED if checksum == expected_checksum else BackupStatus.FAILED
        if status == BackupStatus.FAILED:
            raise ValueError("Checksum do backup nao confere.")
        record = BackupRecord(
            file_path=str(backup_path),
            size_bytes=backup_path.stat().st_size,
            checksum_sha256=checksum,
            status=status,
            notes="Backup verificado por checksum.",
        )
        return BackupResult(record=record, message="Backup verificado com sucesso.")

    def calculate_checksum(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def security_checklist(self, active_users: int, total_permissions: int) -> list[str]:
        return [
            f"Usuarios ativos cadastrados: {active_users}",
            f"Permissoes por perfil registradas: {total_permissions}",
            "Senhas armazenadas com hash PBKDF2.",
            "Acoes sensiveis registradas em logs de auditoria.",
            "Backups locais podem ser verificados por checksum SHA-256.",
        ]
