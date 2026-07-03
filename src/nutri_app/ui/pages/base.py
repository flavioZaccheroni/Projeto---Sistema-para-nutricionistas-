from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Page(QWidget):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)

        self.layout.addWidget(title_label)
        self.layout.addWidget(subtitle_label)

    def add_card(self, widget: QWidget) -> QWidget:
        widget.setObjectName("card")
        self.layout.addWidget(widget)
        return widget
