import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.domain.user import AuthenticatedUser, UserRole
from nutri_app.ui.main_window import MainWindow


class MainWindowMenuSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_window(self) -> MainWindow:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        settings = AppSettings(
            app_name="Nutri Clinic Pro Test",
            organization_name="Nutri Clinic Pro",
            database_path=root / "test.sqlite",
            migrations_path=Path("database/migrations"),
            stylesheet_path=Path("src/nutri_app/ui/resources/app.qss"),
            icon_path=Path("icone.png"),
            seed_data_path=Path("database/seed/starter_foods.csv"),
        )
        context = build_app_context(settings)
        return MainWindow(
            context,
            AuthenticatedUser(1, "Admin", "admin@test.local", UserRole.ADMINISTRADOR),
        )

    def _visible_leaf_titles(self, window: MainWindow) -> set[str]:
        titles: set[str] = set()

        def walk(item):
            for index in range(item.childCount()):
                child = item.child(index)
                if child.childCount() == 0 and not child.isHidden():
                    titles.add(child.text(0))
                walk(child)

        for index in range(window.menu.topLevelItemCount()):
            top = window.menu.topLevelItem(index)
            if top.childCount() == 0:
                if not top.isHidden():
                    titles.add(top.text(0))
            walk(top)
        return titles

    def test_busca_vazia_mostra_tudo(self) -> None:
        window = self._build_window()

        window._filter_menu("")

        self.assertIn("Relatorios", self._visible_leaf_titles(window))
        self.assertIn("Anamnese", self._visible_leaf_titles(window))
        window.close()

    def test_busca_filtra_por_trecho_do_nome_do_modulo(self) -> None:
        window = self._build_window()

        window._filter_menu("relator")

        visible = self._visible_leaf_titles(window)
        self.assertIn("Relatorios", visible)
        self.assertNotIn("Anamnese", visible)
        window.close()

    def test_busca_sem_correspondencia_esconde_tudo(self) -> None:
        window = self._build_window()

        window._filter_menu("xyzxyz-nao-existe")

        self.assertEqual(self._visible_leaf_titles(window), set())
        window.close()

    def test_grupo_pai_fica_visivel_quando_filho_corresponde(self) -> None:
        window = self._build_window()

        window._filter_menu("suplementos")

        clinical_group = window._find_item_by_module("Usuarios").parent()
        self.assertFalse(clinical_group.isHidden())
        window.close()


if __name__ == "__main__":
    unittest.main()
