from __future__ import annotations

from pathlib import Path

from nutri_app.domain.food import FoodSource
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.food import FoodService

STARTER_VERSION = "Conjunto inicial 1.0"
STARTER_LICENSE = (
    "Curadoria interna Nutri Clinic Pro - complementar com a tabela oficial TACO/TBCA "
    "pelo importador de CSV do Banco de Alimentos."
)


def seed_starter_foods(
    connection_factory: SQLiteConnectionFactory,
    csv_path: Path,
) -> int:
    repository = FoodRepository(connection_factory)
    if repository.list_active():
        return 0
    if not csv_path.exists():
        return 0

    foods = FoodService().import_official_csv(
        csv_path,
        FoodSource.REGIONAL,
        STARTER_VERSION,
        STARTER_LICENSE,
    )
    for food in foods:
        repository.add(food)
    return len(foods)
