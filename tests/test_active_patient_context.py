import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.ui.active_patient import ActivePatientContext


class ActivePatientContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_comeca_sem_paciente_ativo(self) -> None:
        context = ActivePatientContext()

        self.assertIsNone(context.patient_id)

    def test_set_patient_atualiza_e_emite_sinal(self) -> None:
        context = ActivePatientContext()
        received: list[int | None] = []
        context.changed.connect(received.append)

        context.set_patient(7)

        self.assertEqual(context.patient_id, 7)
        self.assertEqual(received, [7])

    def test_set_patient_com_mesmo_id_nao_reemite(self) -> None:
        context = ActivePatientContext()
        context.set_patient(7)
        received: list[int | None] = []
        context.changed.connect(received.append)

        context.set_patient(7)

        self.assertEqual(received, [])

    def test_set_patient_none_e_ignorado(self) -> None:
        context = ActivePatientContext()
        context.set_patient(7)
        received: list[int | None] = []
        context.changed.connect(received.append)

        context.set_patient(None)

        self.assertEqual(context.patient_id, 7)
        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
