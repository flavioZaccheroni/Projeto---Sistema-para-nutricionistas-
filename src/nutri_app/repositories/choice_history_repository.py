from __future__ import annotations

from collections import Counter

from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory

# Identificadores fixos (nunca vindos do usuario): origem de cada sugestao.
CHOICE_SOURCES: dict[str, tuple[tuple[str, str], ...]] = {
    "patient_insurance": (("pacientes", "convenio"), ("internacoes", "convenio")),
    "finance_category": (("financeiro_lancamentos", "categoria"),),
    "lab_name": (("exames_laboratoriais", "laboratorio"),),
    "lab_item_name": (("exame_itens", "nome"),),
    "lab_item_unit": (("exame_itens", "unidade"),),
    "supplement_manufacturer": (("suplementos", "fabricante"),),
    "recipe_category": (("receitas", "categoria"),),
    "app_mood": (("paciente_app_adesoes", "humor"),),
    "app_difficulties": (("paciente_app_adesoes", "dificuldades"),),
    "supplement_objective": (("prescricoes_suplementos", "objetivo"),),
}


class ChoiceHistoryRepository:
    """Valores ja digitados em outros registros, para sugerir em campos de texto."""

    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def values(self, source: str, limit: int = 300) -> list[str]:
        counts: Counter[str] = Counter()
        with self.connection_factory.connect() as connection:
            for table, column in CHOICE_SOURCES[source]:
                rows = connection.execute(
                    f"""
                    SELECT TRIM({column}) AS value, COUNT(*) AS uses
                    FROM {table}
                    WHERE deleted_at IS NULL AND {column} IS NOT NULL AND TRIM({column}) != ''
                    GROUP BY TRIM({column})
                    """
                ).fetchall()
                for row in rows:
                    counts[row["value"]] += int(row["uses"])

        by_key: dict[str, Counter[str]] = {}
        for value, uses in counts.items():
            by_key.setdefault(value.lower(), Counter())[value] += uses

        ranked = []
        for variants in by_key.values():
            spelling = sorted(variants.items(), key=lambda item: (-item[1], item[0]))[0][0]
            ranked.append((-sum(variants.values()), spelling.lower(), spelling))
        ranked.sort()
        return [spelling for _uses, _key, spelling in ranked[:limit]]
