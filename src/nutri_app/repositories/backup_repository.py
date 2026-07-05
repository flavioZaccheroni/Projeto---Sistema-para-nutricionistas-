from __future__ import annotations

from datetime import datetime

from nutri_app.domain.backup import BackupRecord, BackupStatus
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class BackupRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, record: BackupRecord) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO backups_sistema (
                    caminho_arquivo, tamanho_bytes, checksum_sha256, status, observacoes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.file_path,
                    record.size_bytes,
                    record.checksum_sha256,
                    record.status.value,
                    record.notes,
                ),
            )
            return int(cursor.lastrowid)

    def update_status(self, backup_id: int, status: BackupStatus, notes: str) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE backups_sistema
                SET status = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (status.value, notes, backup_id),
            )

    def get(self, backup_id: int) -> BackupRecord | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT id, caminho_arquivo, tamanho_bytes, checksum_sha256, status,
                       observacoes, created_at, updated_at
                FROM backups_sistema
                WHERE id = ? AND deleted_at IS NULL
                """,
                (backup_id,),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def list_active(self) -> list[BackupRecord]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, caminho_arquivo, tamanho_bytes, checksum_sha256, status,
                       observacoes, created_at, updated_at
                FROM backups_sistema
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def count_permissions(self) -> int:
        with self.connection_factory.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM perfis_permissao").fetchone()
        return int(row["total"])

    def _row_to_record(self, row) -> BackupRecord:
        return BackupRecord(
            id=row["id"],
            file_path=row["caminho_arquivo"],
            size_bytes=int(row["tamanho_bytes"]),
            checksum_sha256=row["checksum_sha256"],
            status=BackupStatus(row["status"]),
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
