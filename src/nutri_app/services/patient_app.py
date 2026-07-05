from __future__ import annotations

import secrets
import string

from nutri_app.domain.patient_app import (
    PatientAppAccess,
    PatientAppAdherence,
    PatientAppPublication,
)


class PatientAppService:
    def generate_access_code(self, length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def validate_access(self, access: PatientAppAccess) -> None:
        if access.patient_id <= 0:
            raise ValueError("Paciente e obrigatorio para o acesso.")
        if "@" not in access.email_login or "." not in access.email_login:
            raise ValueError("E-mail de login do paciente invalido.")
        if len(access.access_code.strip()) < 6:
            raise ValueError("Codigo de acesso deve ter pelo menos 6 caracteres.")

    def validate_publication(self, publication: PatientAppPublication) -> None:
        if publication.patient_id <= 0:
            raise ValueError("Paciente e obrigatorio para publicar conteudo.")
        if not publication.title.strip():
            raise ValueError("Titulo da publicacao e obrigatorio.")
        if not publication.content.strip():
            raise ValueError("Conteudo da publicacao e obrigatorio.")

    def validate_adherence(self, adherence: PatientAppAdherence) -> None:
        if adherence.patient_id <= 0:
            raise ValueError("Paciente e obrigatorio para registrar adesao.")
        if adherence.adherence_percent < 0 or adherence.adherence_percent > 100:
            raise ValueError("Adesao deve estar entre 0 e 100%.")

    def adherence_classification(self, adherence_percent: float) -> str:
        if adherence_percent >= 85:
            return "Alta adesao"
        if adherence_percent >= 60:
            return "Adesao parcial"
        return "Baixa adesao"
