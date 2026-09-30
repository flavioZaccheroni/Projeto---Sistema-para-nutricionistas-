import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget, QWidget

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.domain.user import AuthenticatedUser, UserRole
from nutri_app.ui.main_window import MainWindow


class MainWindowSaveShortcutTest(unittest.TestCase):
    """Testa apenas o mecanismo de despacho do Ctrl+S (_save_current_page),
    com paginas de mentira, para nao acionar validacoes/dialogos reais das
    telas clinicas."""

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

    def test_ctrl_s_aciona_o_botao_primario_da_pagina_atual(self) -> None:
        window = self._build_window()
        fake_page = QWidget()
        button = QPushButton("Salvar", fake_page)
        button.setObjectName("primaryButton")
        clicks: list[bool] = []
        button.clicked.connect(lambda: clicks.append(True))
        window.pages.addWidget(fake_page)
        window.pages.setCurrentWidget(fake_page)

        window._save_current_page()

        self.assertEqual(clicks, [True])
        window.close()

    def test_ctrl_s_nao_faz_nada_sem_botao_primario(self) -> None:
        window = self._build_window()
        fake_page = QWidget()
        window.pages.addWidget(fake_page)
        window.pages.setCurrentWidget(fake_page)

        window._save_current_page()

        window.close()

    def test_ctrl_s_respeita_a_aba_ativa_quando_a_pagina_tem_abas(self) -> None:
        window = self._build_window()
        fake_page = QWidget()
        fake_page.tabs = QTabWidget(fake_page)

        form_tab = QWidget()
        form_button = QPushButton("Salvar", form_tab)
        form_button.setObjectName("primaryButton")
        fake_page.tabs.addTab(form_tab, "Plano alimentar")

        smart_tab = QWidget()
        smart_button = QPushButton("Calcular / salvar", smart_tab)
        smart_button.setObjectName("primaryButton")
        fake_page.tabs.addTab(smart_tab, "Plano inteligente")

        form_clicks: list[bool] = []
        smart_clicks: list[bool] = []
        form_button.clicked.connect(lambda: form_clicks.append(True))
        smart_button.clicked.connect(lambda: smart_clicks.append(True))

        window.pages.addWidget(fake_page)
        window.pages.setCurrentWidget(fake_page)
        fake_page.tabs.setCurrentIndex(1)

        window._save_current_page()

        self.assertEqual(smart_clicks, [True])
        self.assertEqual(form_clicks, [])
        window.close()


if __name__ == "__main__":
    unittest.main()
