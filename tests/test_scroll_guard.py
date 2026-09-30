import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox, QScrollArea, QWidget

from nutri_app.ui.scroll_guard import ScrollWheelGuard, _find_ancestor_scroll_area


def _make_wheel_event() -> QWheelEvent:
    return QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )


class ScrollWheelGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_find_ancestor_scroll_area_localiza_o_pai_correto(self) -> None:
        scroll_area = QScrollArea()
        content = QWidget()
        combo = QComboBox(content)
        scroll_area.setWidget(content)

        self.assertIs(_find_ancestor_scroll_area(combo), scroll_area)

    def test_find_ancestor_scroll_area_retorna_none_sem_scroll_area(self) -> None:
        content = QWidget()
        combo = QComboBox(content)

        self.assertIsNone(_find_ancestor_scroll_area(combo))

    def test_bloqueia_roda_do_mouse_em_combo_dentro_de_scroll_area(self) -> None:
        scroll_area = QScrollArea()
        content = QWidget()
        combo = QComboBox(content)
        combo.addItems(["3 dobras", "7 dobras"])
        scroll_area.setWidget(content)
        scroll_area.show()

        guard = ScrollWheelGuard()
        handled = guard.eventFilter(combo, _make_wheel_event())

        self.assertTrue(handled)
        self.assertEqual(combo.currentIndex(), 0)

    def test_bloqueia_mesmo_quando_o_combo_esta_com_foco(self) -> None:
        scroll_area = QScrollArea()
        content = QWidget()
        combo = QComboBox(content)
        combo.addItems(["3 dobras", "7 dobras"])
        scroll_area.setWidget(content)
        scroll_area.show()
        combo.setFocus()

        guard = ScrollWheelGuard()
        handled = guard.eventFilter(combo, _make_wheel_event())

        self.assertTrue(handled)
        self.assertEqual(combo.currentIndex(), 0)

    def test_ignora_eventos_que_nao_sao_wheel(self) -> None:
        combo = QComboBox()
        guard = ScrollWheelGuard()
        other_event = QEvent(QEvent.Type.Enter)

        self.assertFalse(guard.eventFilter(combo, other_event))


if __name__ == "__main__":
    unittest.main()
