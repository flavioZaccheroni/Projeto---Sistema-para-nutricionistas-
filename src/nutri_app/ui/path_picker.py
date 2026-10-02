from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget


def with_browse_button(
    field: QLineEdit,
    *,
    title: str,
    folder: bool = False,
    file_filter: str = "",
) -> QWidget:
    """Campo de caminho com botao Procurar; digitar o caminho continua possivel."""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(field, stretch=1)

    button = QPushButton("Procurar...")

    def choose() -> None:
        start = field.text().strip()
        if folder:
            chosen = QFileDialog.getExistingDirectory(container, title, start)
        else:
            chosen, _selected_filter = QFileDialog.getOpenFileName(
                container, title, start, file_filter
            )
        if chosen:
            field.setText(chosen)

    button.clicked.connect(choose)
    layout.addWidget(button)
    container.browse_button = button
    return container
