from __future__ import annotations

from datetime import datetime

from nutri_app.domain.supplement import Supplement, SupplementType
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class SupplementRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, supplement: Supplement) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO suplementos (
                    nome, tipo, fabricante, apresentacao, porcao_base, unidade_porcao,
                    densidade_calorica, osmolaridade_mosm_l, energia_kcal, proteina_g,
                    carboidrato_g, lipidios_g, fibras_g, sodio_mg, composicao,
                    indicacoes, contraindicacoes, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(supplement),
            )
            return int(cursor.lastrowid)

    def update(self, supplement: Supplement) -> None:
        if supplement.id is None:
            raise ValueError("Suplemento sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE suplementos
                SET nome = ?,
                    tipo = ?,
                    fabricante = ?,
                    apresentacao = ?,
                    porcao_base = ?,
                    unidade_porcao = ?,
                    densidade_calorica = ?,
                    osmolaridade_mosm_l = ?,
                    energia_kcal = ?,
                    proteina_g = ?,
                    carboidrato_g = ?,
                    lipidios_g = ?,
                    fibras_g = ?,
                    sodio_mg = ?,
                    composicao = ?,
                    indicacoes = ?,
                    contraindicacoes = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(supplement), supplement.id),
            )

    def soft_delete(self, supplement_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE suplementos
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (supplement_id,),
            )

    def get(self, supplement_id: int) -> Supplement | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"{self._select_sql()} WHERE id = ? AND deleted_at IS NULL",
                (supplement_id,),
            ).fetchone()
        return self._row_to_supplement(row) if row is not None else None

    def list_active(self, query: str = "") -> list[Supplement]:
        normalized = f"%{query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE deleted_at IS NULL
                  AND (
                    ? = '%%'
                    OR lower(nome) LIKE ?
                    OR lower(tipo) LIKE ?
                    OR lower(coalesce(fabricante, '')) LIKE ?
                  )
                ORDER BY nome
                """,
                (normalized, normalized, normalized, normalized),
            ).fetchall()
        return [self._row_to_supplement(row) for row in rows]

    def _values(self, supplement: Supplement) -> tuple:
        return (
            supplement.name,
            supplement.supplement_type.value,
            supplement.manufacturer,
            supplement.presentation,
            supplement.base_portion,
            supplement.portion_unit,
            supplement.caloric_density,
            supplement.osmolarity,
            supplement.energy_kcal,
            supplement.protein_g,
            supplement.carbohydrate_g,
            supplement.fat_g,
            supplement.fiber_g,
            supplement.sodium_mg,
            supplement.composition,
            supplement.indications,
            supplement.contraindications,
            supplement.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT id, nome, tipo, fabricante, apresentacao, porcao_base, unidade_porcao,
                   densidade_calorica, osmolaridade_mosm_l, energia_kcal, proteina_g,
                   carboidrato_g, lipidios_g, fibras_g, sodio_mg, composicao,
                   indicacoes, contraindicacoes, observacoes, created_at, updated_at
            FROM suplementos
        """

    def _row_to_supplement(self, row) -> Supplement:
        return Supplement(
            id=row["id"],
            name=row["nome"],
            supplement_type=SupplementType(row["tipo"]),
            manufacturer=row["fabricante"] or "",
            presentation=row["apresentacao"] or "",
            base_portion=float(row["porcao_base"]),
            portion_unit=row["unidade_porcao"],
            caloric_density=float(row["densidade_calorica"])
            if row["densidade_calorica"] is not None
            else None,
            osmolarity=float(row["osmolaridade_mosm_l"])
            if row["osmolaridade_mosm_l"] is not None
            else None,
            energy_kcal=float(row["energia_kcal"]),
            protein_g=float(row["proteina_g"]),
            carbohydrate_g=float(row["carboidrato_g"]),
            fat_g=float(row["lipidios_g"]),
            fiber_g=float(row["fibras_g"]),
            sodium_mg=float(row["sodio_mg"]),
            composition=row["composicao"] or "",
            indications=row["indicacoes"] or "",
            contraindications=row["contraindicacoes"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
