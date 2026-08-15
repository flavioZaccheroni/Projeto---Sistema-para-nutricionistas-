from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from nutri_app.domain.backup import BackupRecord, BackupStatus


@dataclass(frozen=True)
class BackupResult:
    record: BackupRecord
    message: str


class BackupService:
    encrypted_header = b"NCPBACKUP1"
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

    def create_encrypted_backup(
        self,
        database_path: Path,
        backup_dir: Path,
        passphrase: str,
        note: str = "",
    ) -> BackupResult:
        if len(passphrase) < 12:
            raise ValueError("A senha do backup deve possuir pelo menos 12 caracteres.")
        if not database_path.exists():
            raise ValueError("Banco de dados local nao encontrado para backup.")
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = backup_dir / f"nutri_clinic_pro_{timestamp}.ncpbackup"
        with tempfile.TemporaryDirectory() as tmp:
            temporary_database = Path(tmp) / "backup.sqlite"
            source = sqlite3.connect(database_path)
            destination = sqlite3.connect(temporary_database)
            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()
            salt = os.urandom(16)
            encrypted = self._fernet(passphrase, salt).encrypt(temporary_database.read_bytes())
            output_path.write_bytes(self.encrypted_header + salt + encrypted)
        record = BackupRecord(
            file_path=str(output_path),
            size_bytes=output_path.stat().st_size,
            checksum_sha256=self.calculate_checksum(output_path),
            status=BackupStatus.CREATED,
            notes=(note + " | Backup criptografado AES/Fernet.").strip(" |"),
        )
        return BackupResult(record, "Backup criptografado criado com sucesso.")

    def restore_encrypted_backup(
        self,
        backup_path: Path,
        destination_path: Path,
        passphrase: str,
    ) -> Path:
        payload = backup_path.read_bytes()
        if not payload.startswith(self.encrypted_header) or len(payload) <= 26:
            raise ValueError("Formato de backup criptografado invalido.")
        salt_start = len(self.encrypted_header)
        salt = payload[salt_start : salt_start + 16]
        token = payload[salt_start + 16 :]
        try:
            decrypted = self._fernet(passphrase, salt).decrypt(token)
        except Exception as exc:
            raise ValueError("Senha invalida ou backup corrompido.") from exc
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=destination_path.parent,
            prefix="restore_",
            suffix=".sqlite",
            delete=False,
        ) as temporary:
            temporary.write(decrypted)
            temporary_path = Path(temporary.name)
        try:
            connection = sqlite3.connect(temporary_path)
            try:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                connection.close()
            if integrity != "ok":
                raise ValueError(f"Falha na integridade SQLite: {integrity}")
            temporary_path.replace(destination_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
        return destination_path

    def prune_backups(
        self,
        backup_dir: Path,
        retention_days: int,
        now: datetime | None = None,
    ) -> int:
        if retention_days < 1:
            raise ValueError("Retencao deve ser de pelo menos 1 dia.")
        if not backup_dir.exists():
            return 0
        reference = (now or datetime.now()).timestamp()
        limit_seconds = retention_days * 24 * 60 * 60
        removed = 0
        for path in backup_dir.glob("nutri_clinic_pro_*"):
            if path.is_file() and reference - path.stat().st_mtime > limit_seconds:
                path.unlink()
                removed += 1
        return removed

    def calculate_checksum(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _fernet(self, passphrase: str, salt: bytes):
        import base64

        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
        except ImportError as exc:
            raise ValueError(
                "Dependencia cryptography ausente; instale requirements.txt."
            ) from exc
        kdf = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1)
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))
        return Fernet(key)

    def security_checklist(self, active_users: int, total_permissions: int) -> list[str]:
        return [
            f"Usuarios ativos cadastrados: {active_users}",
            f"Permissoes por perfil registradas: {total_permissions}",
            "Senhas armazenadas com hash PBKDF2.",
            "Acoes sensiveis registradas em logs de auditoria.",
            "Backups locais podem ser verificados por checksum SHA-256.",
            "Backups criptografados usam chave derivada por Scrypt e AES/Fernet.",
        ]
