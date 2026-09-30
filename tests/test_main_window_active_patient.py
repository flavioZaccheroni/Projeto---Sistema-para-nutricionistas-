import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.domain.patient import Patient
from nutri_app.domain.user import AuthenticatedUser, UserRole
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.ui.main_window import MainWindow


class MainWindowActivePatientTest(unittest.TestCase):
    """Reproduz o cenario relatado: selecionar um paciente na Agenda e, ao
    abrir outra tela clinica, o paciente selecionado deve continuar sendo
    o mesmo, em vez de cada tela lembrar o proprio ultimo paciente."""

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
        patient_repository = PatientRepository(context.connection_factory)
        self.ana_id = patient_repository.add(
            Patient(name="Ana Teste", birth_date=date(1990, 1, 1))
        )
        self.bruno_id = patient_repository.add(
            Patient(name="Bruno Teste", birth_date=date(1985, 5, 5))
        )
        return MainWindow(
            context,
            AuthenticatedUser(1, "Admin", "admin@test.local", UserRole.ADMINISTRADOR),
        )

    def _show(self, window: MainWindow, module: str):
        item = window._find_item_by_module(module)
        window._show_page(item)
        return window.pages.currentWidget()

    def test_paciente_selecionado_na_agenda_aparece_na_anamnese(self) -> None:
        window = self._build_window()

        agenda_page = self._show(window, "Agenda")
        index = agenda_page.patient_ids_by_index.index(self.bruno_id)
        agenda_page.patient.setCurrentIndex(index)

        self.assertEqual(window.active_patient.patient_id, self.bruno_id)

        anamnesis_page = self._show(window, "Anamnese")
        selected_id = anamnesis_page.patient_ids_by_index[anamnesis_page.patient.currentIndex()]

        self.assertEqual(selected_id, self.bruno_id)
        window.close()

    def test_navegar_entre_varias_telas_mantem_o_mesmo_paciente(self) -> None:
        window = self._build_window()

        anamnesis_page = self._show(window, "Anamnese")
        index = anamnesis_page.patient_ids_by_index.index(self.ana_id)
        anamnesis_page.patient.setCurrentIndex(index)

        for module in ["Antropometria", "Composicao Corporal", "Gasto Energetico"]:
            page = self._show(window, module)
            selected_id = page.patient_ids_by_index[page.patient.currentIndex()]
            self.assertEqual(selected_id, self.ana_id, f"Falhou em {module}")

        window.close()

    def test_paginas_com_patient_ids_sem_sufixo_tambem_sincronizam(self) -> None:
        """Avaliacao Clinica e os modulos genericos (advanced_module_page)
        usam self.patient_ids em vez de self.patient_ids_by_index."""
        window = self._build_window()

        anamnesis_page = self._show(window, "Anamnese")
        index = anamnesis_page.patient_ids_by_index.index(self.bruno_id)
        anamnesis_page.patient.setCurrentIndex(index)

        for module in ["Avaliacao Clinica", "Protocolos Clinicos"]:
            page = self._show(window, module)
            selected_id = page.patient_ids[page.patient.currentIndex()]
            self.assertEqual(selected_id, self.bruno_id, f"Falhou em {module}")

        window.close()

    def test_botao_atender_leva_para_anamnese_com_o_paciente_certo(self) -> None:
        window = self._build_window()

        agenda_page = self._show(window, "Agenda")
        index = agenda_page.patient_ids_by_index.index(self.bruno_id)
        agenda_page.patient.setCurrentIndex(index)

        agenda_page._request_attend()

        self.assertEqual(
            window.pages.currentIndex(), window.page_indexes_by_module["Anamnese"]
        )
        anamnesis_page = window.pages.currentWidget()
        selected_id = anamnesis_page.patient_ids_by_index[anamnesis_page.patient.currentIndex()]
        self.assertEqual(selected_id, self.bruno_id)
        self.assertEqual(window.active_patient.patient_id, self.bruno_id)

        window.close()


if __name__ == "__main__":
    unittest.main()
