from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from nutri_app.app.settings import AppSettings


class AppSettingsTest(unittest.TestCase):
    def test_modo_desenvolvimento_mantem_dados_no_projeto(self) -> None:
        settings = AppSettings.load()

        self.assertEqual(settings.data_dir, Path(__file__).resolve().parents[1])
        self.assertEqual(settings.exports_dir, settings.data_dir / "exports")
        self.assertEqual(settings.backups_dir, settings.data_dir / "backups")

    def test_executavel_isola_dados_no_perfil_do_usuario(self) -> None:
        with TemporaryDirectory() as tmp:
            local_app_data = Path(tmp) / "AppData" / "Local"
            resource_root = Path(tmp) / "recursos"
            with (
                patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}),
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(resource_root), create=True),
            ):
                settings = AppSettings.load()

        expected_data_dir = local_app_data / "Nutri Clinic Pro"
        self.assertEqual(settings.data_dir, expected_data_dir)
        self.assertEqual(settings.database_path, expected_data_dir / "nutri_app.sqlite")
        self.assertEqual(settings.exports_dir, expected_data_dir / "exports")
        self.assertEqual(settings.backups_dir, expected_data_dir / "backups")
        self.assertEqual(
            settings.migrations_path,
            resource_root / "database" / "migrations",
        )
        self.assertEqual(
            settings.stylesheet_path,
            resource_root / "nutri_app" / "ui" / "resources" / "app.qss",
        )


if __name__ == "__main__":
    unittest.main()
