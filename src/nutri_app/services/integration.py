from __future__ import annotations

import json
from datetime import date

from nutri_app.domain.integration import ExternalIntegration
from nutri_app.domain.laboratory_exam import LaboratoryExam, LaboratoryExamItem


class IntegrationService:
    def validate_integration(self, integration: ExternalIntegration) -> None:
        if not integration.name.strip():
            raise ValueError("Nome da integracao e obrigatorio.")
        if integration.endpoint and not (
            integration.endpoint.startswith("http://")
            or integration.endpoint.startswith("https://")
            or integration.endpoint.startswith("file://")
        ):
            raise ValueError("Endpoint deve iniciar com http://, https:// ou file://.")

    def parse_laboratory_payload(self, payload: str, patient_id: int) -> LaboratoryExam:
        if patient_id <= 0:
            raise ValueError("Paciente e obrigatorio para importar exame.")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Payload laboratorial deve estar em JSON valido.") from exc

        items = [
            LaboratoryExamItem(
                name=str(item.get("nome", "")).strip(),
                value=self._optional_float(item.get("valor")),
                unit=str(item.get("unidade", "")).strip(),
                reference=str(item.get("referencia", "")).strip(),
                alert=str(item.get("alerta", "")).strip(),
            )
            for item in data.get("itens", [])
        ]
        if not items or any(not item.name for item in items):
            raise ValueError("Payload deve conter itens de exame com nome.")

        return LaboratoryExam(
            patient_id=patient_id,
            exam_date=date.fromisoformat(data.get("data_exame", date.today().isoformat())),
            laboratory=str(data.get("laboratorio", "")).strip(),
            notes=str(data.get("observacoes", "")).strip(),
            items=items,
        )

    def simulate_sync(self, integration: ExternalIntegration, entity: str) -> str:
        self.validate_integration(integration)
        return f"Integracao {integration.name} pronta para sincronizar {entity}."

    def _optional_float(self, value: object) -> float | None:
        if value in [None, ""]:
            return None
        return float(value)
