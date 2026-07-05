from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.patient_app import (
    PatientAppAccess,
    PatientAppAdherence,
    PatientAppPublication,
    PatientAppSummary,
    PatientPublicationStatus,
    PatientPublicationType,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientAppRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def upsert_access(self, access: PatientAppAccess) -> int:
        with self.connection_factory.connect() as connection:
            existing = connection.execute(
                """
                SELECT id FROM paciente_app_acessos
                WHERE paciente_id = ? AND deleted_at IS NULL
                """,
                (access.patient_id,),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE paciente_app_acessos
                    SET email_login = ?,
                        codigo_acesso = ?,
                        ativo = ?,
                        observacoes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        access.email_login,
                        access.access_code,
                        1 if access.active else 0,
                        access.notes,
                        existing["id"],
                    ),
                )
                return int(existing["id"])
            cursor = connection.execute(
                """
                INSERT INTO paciente_app_acessos (
                    paciente_id, email_login, codigo_acesso, ativo, observacoes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    access.patient_id,
                    access.email_login,
                    access.access_code,
                    1 if access.active else 0,
                    access.notes,
                ),
            )
            return int(cursor.lastrowid)

    def add_publication(self, publication: PatientAppPublication) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO paciente_app_publicacoes (
                    paciente_id, plano_id, tipo, titulo, conteudo, status,
                    data_publicacao, data_expiracao, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    publication.patient_id,
                    publication.meal_plan_id,
                    publication.publication_type.value,
                    publication.title,
                    publication.content,
                    publication.status.value,
                    publication.publication_date.isoformat(),
                    publication.expiration_date.isoformat()
                    if publication.expiration_date is not None
                    else None,
                    publication.notes,
                ),
            )
            return int(cursor.lastrowid)

    def add_adherence(self, adherence: PatientAppAdherence) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO paciente_app_adesoes (
                    paciente_id, publicacao_id, data_registro, percentual_adesao,
                    humor, dificuldades, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adherence.patient_id,
                    adherence.publication_id,
                    adherence.record_date.isoformat(),
                    adherence.adherence_percent,
                    adherence.mood,
                    adherence.difficulties,
                    adherence.notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_accesses(self, patient_query: str = "") -> list[PatientAppAccess]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT a.id, a.paciente_id, p.nome AS paciente_nome, a.email_login,
                       a.codigo_acesso, a.ativo, a.ultimo_acesso, a.observacoes,
                       a.created_at, a.updated_at
                FROM paciente_app_acessos a
                JOIN pacientes p ON p.id = a.paciente_id
                WHERE a.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY p.nome
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_access(row) for row in rows]

    def list_publications(self, patient_query: str = "") -> list[PatientAppPublication]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT pub.id, pub.paciente_id, p.nome AS paciente_nome, pub.plano_id,
                       CASE
                           WHEN pa.id IS NULL THEN ''
                           ELSE pa.data_inicio || ' - ' || pa.objetivo
                       END AS plano_rotulo,
                       pub.tipo, pub.titulo, pub.conteudo, pub.status,
                       pub.data_publicacao, pub.data_expiracao, pub.observacoes,
                       pub.created_at, pub.updated_at
                FROM paciente_app_publicacoes pub
                JOIN pacientes p ON p.id = pub.paciente_id
                LEFT JOIN planos_alimentares pa ON pa.id = pub.plano_id
                WHERE pub.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY pub.data_publicacao DESC, pub.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_publication(row) for row in rows]

    def list_adherences(self, patient_query: str = "") -> list[PatientAppAdherence]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT ad.id, ad.paciente_id, p.nome AS paciente_nome, ad.publicacao_id,
                       pub.titulo AS publicacao_titulo, ad.data_registro,
                       ad.percentual_adesao, ad.humor, ad.dificuldades, ad.observacoes,
                       ad.created_at, ad.updated_at
                FROM paciente_app_adesoes ad
                JOIN pacientes p ON p.id = ad.paciente_id
                LEFT JOIN paciente_app_publicacoes pub ON pub.id = ad.publicacao_id
                WHERE ad.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY ad.data_registro DESC, ad.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_adherence(row) for row in rows]

    def summary(self) -> PatientAppSummary:
        with self.connection_factory.connect() as connection:
            access = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM paciente_app_acessos
                WHERE ativo = 1 AND deleted_at IS NULL
                """
            ).fetchone()
            publications = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM paciente_app_publicacoes
                WHERE status = ? AND deleted_at IS NULL
                """,
                (PatientPublicationStatus.PUBLISHED.value,),
            ).fetchone()
            adherence = connection.execute(
                """
                SELECT AVG(percentual_adesao) AS media
                FROM paciente_app_adesoes
                WHERE deleted_at IS NULL
                """
            ).fetchone()
        return PatientAppSummary(
            total_accesses=int(access["total"]),
            total_published=int(publications["total"]),
            average_adherence=float(adherence["media"] or 0),
        )

    def _row_to_access(self, row) -> PatientAppAccess:
        return PatientAppAccess(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            email_login=row["email_login"],
            access_code=row["codigo_acesso"],
            active=bool(row["ativo"]),
            last_access=datetime.fromisoformat(row["ultimo_acesso"])
            if row["ultimo_acesso"]
            else None,
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_publication(self, row) -> PatientAppPublication:
        return PatientAppPublication(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            meal_plan_id=row["plano_id"],
            meal_plan_label=row["plano_rotulo"] or "",
            publication_type=PatientPublicationType(row["tipo"]),
            title=row["titulo"],
            content=row["conteudo"],
            status=PatientPublicationStatus(row["status"]),
            publication_date=date.fromisoformat(row["data_publicacao"]),
            expiration_date=date.fromisoformat(row["data_expiracao"])
            if row["data_expiracao"]
            else None,
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_adherence(self, row) -> PatientAppAdherence:
        return PatientAppAdherence(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            publication_id=row["publicacao_id"],
            publication_title=row["publicacao_titulo"] or "",
            record_date=date.fromisoformat(row["data_registro"]),
            adherence_percent=float(row["percentual_adesao"]),
            mood=row["humor"] or "",
            difficulties=row["dificuldades"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
