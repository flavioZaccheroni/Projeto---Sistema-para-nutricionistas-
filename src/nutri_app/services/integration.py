from __future__ import annotations

import json
import os
import time
import uuid
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from nutri_app.domain.integration import ExternalIntegration, IntegrationDirection
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

    def execute_sync(
        self,
        integration: ExternalIntegration,
        entity: str,
        payload: str,
        direction: IntegrationDirection = IntegrationDirection.EXPORT,
        timeout_seconds: int = 15,
        max_retries: int = 3,
        idempotency_key: str | None = None,
    ) -> str:
        self.validate_integration(integration)
        if not integration.endpoint:
            raise ValueError("Endpoint e obrigatorio para sincronizacao real.")
        try:
            parsed_payload = json.loads(payload or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("Payload de sincronizacao deve ser JSON valido.") from exc
        parsed_url = urlparse(integration.endpoint)
        if parsed_url.scheme == "file":
            return self._execute_file_sync(
                Path(parsed_url.path.lstrip("/") if os.name == "nt" else parsed_url.path),
                parsed_payload,
                direction,
            )
        credential = ""
        if integration.credential_alias:
            credential = os.getenv(integration.credential_alias, "")
            if not credential:
                raise ValueError(
                    f"Credencial nao encontrada no ambiente: {integration.credential_alias}"
                )
        body = json.dumps(
            {"entity": entity, "data": parsed_payload}, ensure_ascii=False
        ).encode("utf-8")
        key = idempotency_key or str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Idempotency-Key": key,
            "User-Agent": "Nutri-Clinic-Pro/1.0",
        }
        if credential:
            headers["Authorization"] = f"Bearer {credential}"
        last_error: Exception | None = None
        for attempt in range(max_retries):
            request = Request(integration.endpoint, data=body, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=timeout_seconds) as response:
                    response_body = response.read().decode("utf-8", errors="replace")
                    return (
                        f"HTTP {response.status}; idempotencia={key}; "
                        f"resposta={response_body[:1000]}"
                    )
            except (HTTPError, URLError, TimeoutError) as exc:
                last_error = exc
                if isinstance(exc, HTTPError) and exc.code < 500 and exc.code != 429:
                    break
                if attempt + 1 < max_retries:
                    time.sleep(min(2**attempt, 4))
        raise ValueError(f"Falha na sincronizacao apos {max_retries} tentativa(s): {last_error}")

    def _execute_file_sync(
        self,
        path: Path,
        payload: object,
        direction: IntegrationDirection,
    ) -> str:
        if direction == IntegrationDirection.IMPORT:
            if not path.exists():
                raise ValueError("Arquivo de integracao nao encontrado.")
            json.loads(path.read_text(encoding="utf-8"))
            return f"Importacao local validada: {path}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"Exportacao local concluida: {path}"

    def _optional_float(self, value: object) -> float | None:
        if value in [None, ""]:
            return None
        return float(value)
