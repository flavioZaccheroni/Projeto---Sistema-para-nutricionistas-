from __future__ import annotations

import os
import sys
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
    data_dir: Path | None = None

    @property
    def user_data_dir(self) -> Path:
        return self.data_dir or self.database_path.parent

    @property
    def exports_dir(self) -> Path:
        return self.user_data_dir / "exports"

    @property
    def backups_dir(self) -> Path:
        return self.user_data_dir / "backups"

    @classmethod
    def load(cls) -> AppSettings:
        if getattr(sys, "frozen", False):
            resource_root = Path(sys._MEIPASS)
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
            )
            data_dir = local_app_data / "Nutri Clinic Pro"
            return cls(
                app_name="Nutri Clinic Pro",
                organization_name="Nutri Clinic Pro",
                database_path=data_dir / "nutri_app.sqlite",
                migrations_path=resource_root / "database" / "migrations",
                stylesheet_path=resource_root / "nutri_app" / "ui" / "resources" / "app.qss",
                icon_path=resource_root / "icone.png",
                data_dir=data_dir,
            )

        root = Path(__file__).resolve().parents[3]
        return cls(
            app_name="Nutri Clinic Pro",
            organization_name="Nutri Clinic Pro",
            database_path=root / "database" / "local" / "nutri_app.sqlite",
            migrations_path=root / "database" / "migrations",
            stylesheet_path=root / "src" / "nutri_app" / "ui" / "resources" / "app.qss",
            icon_path=root / "icone.png",
            data_dir=root,
        )
