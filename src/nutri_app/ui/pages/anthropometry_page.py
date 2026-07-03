from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from nutri_app.services.anthropometry import AnthropometryService
from nutri_app.ui.pages.base import Page


class AnthropometryPage(Page):
    def __init__(self) -> None:
        super().__init__("Antropometria", "Medidas corporais e indicadores automaticos.")
        self.service = AnthropometryService()
        self.weight = QLineEdit()
        self.height = QLineEdit()
        self.result = QLabel("Informe peso e altura para calcular o IMC.")

        form = QFormLayout()
        form.addRow("Peso (kg)", self.weight)
        form.addRow("Altura (m)", self.height)

        calculate = QPushButton("Calcular IMC")
        calculate.clicked.connect(self._calculate_bmi)

        actions = QHBoxLayout()
        actions.addWidget(calculate)
        actions.addStretch()

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)
        wrapper_layout.addRow("Resultado", self.result)

        self.layout.addWidget(wrapper)
        self.layout.addStretch()

    def _calculate_bmi(self) -> None:
        try:
            weight = float(self.weight.text().replace(",", "."))
            height = float(self.height.text().replace(",", "."))
            bmi = self.service.calculate_bmi(weight, height)
            classification = self.service.classify_adult_bmi(bmi)
        except ValueError as exc:
            self.result.setText(str(exc) or "Preencha valores numericos validos.")
            return

        self.result.setText(f"IMC {bmi:.1f} - {classification.value}")
