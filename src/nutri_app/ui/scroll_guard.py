from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QScrollArea,
    QSlider,
    QWidget,
)

_GUARDED_TYPES = (QComboBox, QAbstractSpinBox, QSlider)


class ScrollWheelGuard(QObject):
    """Evita que a roda do mouse altere um combo/spinbox/slider dentro de uma
    tela rolavel; a rolagem e sempre repassada para a QScrollArea envolvente.
    """

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.Wheel or not isinstance(watched, _GUARDED_TYPES):
            return False

        scroll_area = _find_ancestor_scroll_area(watched)
        if scroll_area is not None:
            QApplication.sendEvent(scroll_area.viewport(), event)
        return True


def _find_ancestor_scroll_area(widget: QWidget) -> QScrollArea | None:
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QScrollArea):
            return parent
        parent = parent.parentWidget()
    return None


def install_scroll_wheel_guard(app: QApplication) -> ScrollWheelGuard:
    guard = ScrollWheelGuard(app)
    app.installEventFilter(guard)
    return guard
