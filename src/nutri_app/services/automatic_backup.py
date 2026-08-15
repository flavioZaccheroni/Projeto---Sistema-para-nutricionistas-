from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.backup_repository import BackupRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.backup import BackupResult, BackupService


def run_configured_automatic_backup(
    connection_factory: SQLiteConnectionFactory,
    database_path: Path,
    now: datetime | None = None,
) -> BackupResult | None:
    """Create an encrypted startup backup when the configured interval is due.

    The passphrase and external destination deliberately come from environment
    variables so no backup secret is persisted in the clinical database.
    """
    audit = AuditRepository(connection_factory)
    with connection_factory.connect() as connection:
        rows = connection.execute(
            """
            SELECT chave, valor FROM configuracoes
            WHERE chave IN (
                'backup_automatico_ativo', 'backup_intervalo_horas',
                'backup_retencao_dias'
            ) AND deleted_at IS NULL
            """
        ).fetchall()
        configuration = {row["chave"]: row["valor"] for row in rows}
        latest = connection.execute(
            """
            SELECT created_at FROM backups_sistema
            WHERE deleted_at IS NULL AND caminho_arquivo LIKE '%.ncpbackup'
            ORDER BY created_at DESC, id DESC LIMIT 1
            """
        ).fetchone()

    if configuration.get("backup_automatico_ativo", "0") != "1":
        return None
    passphrase = os.getenv("NUTRI_BACKUP_PASSPHRASE", "")
    destination = os.getenv("NUTRI_BACKUP_DIR", "")
    if len(passphrase) < 12 or not destination:
        audit.log(
            None,
            "backup_automatico_nao_executado",
            "backups_sistema",
            None,
            "Defina NUTRI_BACKUP_DIR e NUTRI_BACKUP_PASSPHRASE (12+ caracteres).",
        )
        return None

    reference = now or datetime.now()
    interval = max(1, int(configuration.get("backup_intervalo_horas", "24")))
    if latest is not None:
        last_created = datetime.fromisoformat(latest["created_at"])
        if reference - last_created < timedelta(hours=interval):
            return None

    backup_dir = Path(destination).expanduser().resolve()
    service = BackupService()
    result = service.create_encrypted_backup(
        database_path,
        backup_dir,
        passphrase,
        "Backup automatico de inicializacao.",
    )
    backup_id = BackupRepository(connection_factory).add(result.record)
    retention = max(1, int(configuration.get("backup_retencao_dias", "30")))
    service.prune_backups(backup_dir, retention, reference)
    audit.log(
        None,
        "criou_backup_automatico_criptografado",
        "backups_sistema",
        backup_id,
        str(backup_dir),
    )
    return result
