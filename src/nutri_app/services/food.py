from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from nutri_app.domain.food import Food, FoodSource


@dataclass(frozen=True)
class PortionNutrients:
    energy_kcal: float
    protein_g: float
    carbohydrate_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float


class FoodService:
    def validate(self, food: Food) -> None:
        if not food.name.strip():
            raise ValueError("Nome do alimento deve ser informado.")
        if food.base_portion_g <= 0:
            raise ValueError("Porcao base deve ser maior que zero.")
        numeric_values = [
            food.energy_kcal,
            food.protein_g,
            food.carbohydrate_g,
            food.fat_g,
            food.fiber_g,
            food.sodium_mg,
        ]
        if any(value < 0 for value in numeric_values):
            raise ValueError("Valores nutricionais nao podem ser negativos.")
        if food.glycemic_index is not None and food.glycemic_index < 0:
            raise ValueError("Indice glicemico nao pode ser negativo.")

    def calculate_portion(self, food: Food, portion_g: float) -> PortionNutrients:
        self.validate(food)
        if portion_g <= 0:
            raise ValueError("Porcao calculada deve ser maior que zero.")
        factor = portion_g / food.base_portion_g
        return PortionNutrients(
            energy_kcal=food.energy_kcal * factor,
            protein_g=food.protein_g * factor,
            carbohydrate_g=food.carbohydrate_g * factor,
            fat_g=food.fat_g * factor,
            fiber_g=food.fiber_g * factor,
            sodium_mg=food.sodium_mg * factor,
        )

    def import_official_csv(
        self,
        file_path: Path,
        source: FoodSource,
        version: str,
        license_name: str,
    ) -> list[Food]:
        if source not in {FoodSource.TACO, FoodSource.TBCA, FoodSource.REGIONAL}:
            raise ValueError("Selecione uma fonte oficial ou regional para importacao.")
        if not version.strip() or not license_name.strip():
            raise ValueError("Versao e licenca da fonte sao obrigatorias.")
        foods: list[Food] = []
        with file_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"nome", "energia_kcal", "proteina_g", "carboidrato_g", "lipidios_g"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise ValueError(
                    "CSV deve conter nome, energia_kcal, proteina_g, carboidrato_g e lipidios_g."
                )
            for row_number, row in enumerate(reader, 2):
                try:
                    food = Food(
                        name=row["nome"].strip(),
                        source=source,
                        category=row.get("categoria", "").strip(),
                        base_portion_g=self._csv_float(row.get("porcao_base_g"), 100),
                        household_measure=row.get("medida_caseira", "").strip(),
                        energy_kcal=self._csv_float(row["energia_kcal"]),
                        protein_g=self._csv_float(row["proteina_g"]),
                        carbohydrate_g=self._csv_float(row["carboidrato_g"]),
                        fat_g=self._csv_float(row["lipidios_g"]),
                        fiber_g=self._csv_float(row.get("fibras_g")),
                        sodium_mg=self._csv_float(row.get("sodio_mg")),
                        micronutrients=row.get("micronutrientes", "").strip(),
                        notes=(
                            f"Importado de {source.value}; versao {version.strip()}; "
                            f"licenca {license_name.strip()}."
                        ),
                    )
                    self.validate(food)
                except (ValueError, AttributeError) as exc:
                    raise ValueError(f"Linha {row_number} do CSV invalida: {exc}") from exc
                foods.append(food)
        if not foods:
            raise ValueError("O CSV nao possui alimentos para importar.")
        return foods

    def _csv_float(self, value: str | None, default: float = 0) -> float:
        text = (value or "").strip()
        return default if not text else float(text.replace(",", "."))
