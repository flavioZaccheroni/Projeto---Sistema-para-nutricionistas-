from __future__ import annotations


class LaboratoryExamService:
    def build_reference(self, minimum: float | None, maximum: float | None) -> str:
        if minimum is None and maximum is None:
            return ""
        if minimum is None:
            return f"<= {maximum:g}"
        if maximum is None:
            return f">= {minimum:g}"
        return f"{minimum:g} - {maximum:g}"

    def classify_alert(
        self,
        value: float | None,
        minimum: float | None,
        maximum: float | None,
    ) -> str:
        if value is None:
            return ""
        if minimum is not None and value < minimum:
            return "abaixo da referencia"
        if maximum is not None and value > maximum:
            return "acima da referencia"
        return ""

    def validate_item_name(self, name: str) -> None:
        if not name.strip():
            raise ValueError("Nome do exame deve ser informado.")
