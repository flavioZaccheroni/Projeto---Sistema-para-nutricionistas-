import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit

from nutri_app.database.schema import initialize_database
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.recipes_page import RecipesPage
from nutri_app.ui.pages.web_portal_page import WebPortalPage
from nutri_app.ui.path_picker import with_browse_button

MODULE = "nutri_app.ui.path_picker.QFileDialog"


class PathPickerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_arquivo_escolhido_vai_para_o_campo(self) -> None:
        field = QLineEdit()
        container = with_browse_button(field, title="Foto", file_filter="Imagens (*.png)")

        with patch(f"{MODULE}.getOpenFileName", return_value=("C:/fotos/prato.png", "")) as dialog:
            container.browse_button.click()

        self.assertEqual(field.text(), "C:/fotos/prato.png")
        self.assertEqual(dialog.call_args.args[1], "Foto")

    def test_cancelar_nao_altera_o_que_ja_estava_digitado(self) -> None:
        field = QLineEdit("C:/antigo.png")
        container = with_browse_button(field, title="Foto")

        with patch(f"{MODULE}.getOpenFileName", return_value=("", "")):
            container.browse_button.click()

        self.assertEqual(field.text(), "C:/antigo.png")

    def test_modo_pasta_usa_o_seletor_de_diretorio(self) -> None:
        field = QLineEdit("C:/saida")
        container = with_browse_button(field, title="Pasta", folder=True)

        with patch(f"{MODULE}.getExistingDirectory", return_value="C:/nova") as dialog:
            container.browse_button.click()

        self.assertEqual(field.text(), "C:/nova")
        self.assertEqual(dialog.call_args.args[2], "C:/saida")

    def test_o_campo_continua_digitavel_dentro_do_container(self) -> None:
        field = QLineEdit()
        container = with_browse_button(field, title="Foto")

        field.setText("D:/manual.png")

        self.assertIs(field.parentWidget(), container)
        self.assertEqual(field.text(), "D:/manual.png")

    def test_telas_de_receitas_e_portal_web_tem_o_botao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "t.sqlite")
            initialize_database(factory)
            audit = AuditRepository(factory)

            recipes = RecipesPage(factory, audit, current_user_id=1)
            portal = WebPortalPage(factory, audit, current_user_id=1)

            self.assertTrue(hasattr(recipes.photo_path.parentWidget(), "browse_button"))
            self.assertTrue(hasattr(portal.output_dir.parentWidget(), "browse_button"))


if __name__ == "__main__":
    unittest.main()
