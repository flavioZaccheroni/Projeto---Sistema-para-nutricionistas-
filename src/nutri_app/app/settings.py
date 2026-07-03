from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    app_name: str
    organization_name: str
    database_path: Path
    migrations_path: Path
    stylesheet_path: Path
    icon_path: Path

    @classmethod
    def load(cls) -> "AppSettings":
        root = Path(__file__).resolve().parents[3]
        return cls(
            app_name="Nutri Clinic Pro",
            organization_name="Nutri Clinic Pro",
            database_path=root / "database" / "local" / "nutri_app.sqlite",
            migrations_path=root / "database" / "migrations",
            stylesheet_path=root / "src" / "nutri_app" / "ui" / "resources" / "app.qss",
            icon_path=root / "icone.png",
        )
