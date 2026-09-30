from __future__ import annotations

from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class Page(QWidget):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()

        content = QWidget()
        content.setObjectName("pageContent")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)

        self.layout.addWidget(title_label)
        self.layout.addWidget(subtitle_label)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("pageScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setWidget(content)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)

    def add_card(self, widget: QWidget) -> QWidget:
        widget.setObjectName("card")
        self.layout.addWidget(widget)
        return widget
