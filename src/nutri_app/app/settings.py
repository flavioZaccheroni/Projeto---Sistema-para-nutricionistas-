from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    app_name: str
    organization_name: str
    database_path: Path

    @classmethod
    def load(cls) -> "AppSettings":
        root = Path(__file__).resolve().parents[3]
        return cls(
            app_name="Sistema Profissional para Nutricionistas",
            organization_name="Projeto Sistema Nutricionistas",
            database_path=root / "database" / "local" / "nutri_app.sqlite",
        )
