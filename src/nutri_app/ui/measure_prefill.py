from __future__ import annotations

from PySide6.QtWidgets import QLineEdit

from nutri_app.domain.patient import Patient
from nutri_app.repositories.anthropometry_repository import AnthropometryRepository
from nutri_app.services.measure_suggestion import MeasureSuggestion, suggest_measures
from nutri_app.ui.date_format import format_date

FIELD_KEYS = ("age", "age_months", "weight", "height", "waist", "hip")


class MeasurePrefill:
    """Preenche idade/peso/altura a partir do paciente e da ultima antropometria.

    Lembra o que escreveu em cada campo: ao trocar de paciente, troca so os
    valores que foram preenchidos por aqui (ou estao vazios) e nunca sobrescreve
    o que o usuario digitou.
    """

    def __init__(
        self,
        repository: AnthropometryRepository,
        fields: dict[str, QLineEdit],
    ) -> None:
        unknown = set(fields) - set(FIELD_KEYS)
        if unknown:
            raise ValueError(f"Campos desconhecidos: {sorted(unknown)}")
        self.repository = repository
        self.fields = fields
        self._auto_values: dict[str, str] = {}

    def apply(self, patient: Patient | None) -> None:
        if patient is None or patient.id is None:
            suggestion, note = None, ""
        else:
            latest = self.repository.latest_for_patient(patient.id)
            suggestion = suggest_measures(patient.birth_date, latest)
            note = self._source_note(suggestion)

        for key, field in self.fields.items():
            new_text = self._text_for(key, suggestion)
            current = field.text().strip()
            if current and current != self._auto_values.get(key):
                continue
            field.setText(new_text)
            field.setToolTip(note if new_text and key not in ("age", "age_months") else "")
            self._auto_values[key] = new_text

    def _text_for(self, key: str, suggestion: MeasureSuggestion | None) -> str:
        if suggestion is None:
            return ""
        value = {
            "age": suggestion.age_years,
            "age_months": suggestion.age_months,
            "weight": suggestion.weight_kg,
            "height": suggestion.height_cm,
            "waist": suggestion.waist_cm,
            "hip": suggestion.hip_cm,
        }[key]
        if value is None:
            return ""
        return f"{value:g}" if isinstance(value, float) else str(value)

    def _source_note(self, suggestion: MeasureSuggestion) -> str:
        if suggestion.source_date is None:
            return ""
        return f"Preenchido da antropometria de {format_date(suggestion.source_date)}."
