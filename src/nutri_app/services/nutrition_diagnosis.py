from __future__ import annotations

from nutri_app.domain.nutrition_diagnosis import DiagnosisProtocol, DiagnosisSeverity


class NutritionDiagnosisService:
    def classify(
        self,
        protocol: DiagnosisProtocol,
        primary_criteria: int,
        secondary_criteria: int,
        severe_marker: bool = False,
    ) -> tuple[str, DiagnosisSeverity]:
        if primary_criteria < 0 or secondary_criteria < 0:
            raise ValueError("Criterios nao podem ser negativos.")

        if protocol == DiagnosisProtocol.GLIM:
            positive = primary_criteria >= 1 and secondary_criteria >= 1
            if not positive:
                return "GLIM negativo", DiagnosisSeverity.NONE
            severity = DiagnosisSeverity.SEVERE if severe_marker else DiagnosisSeverity.MODERATE
            return "desnutricao relacionada a doenca", severity

        if protocol in {
            DiagnosisProtocol.ASPEN,
            DiagnosisProtocol.ESPEN,
            DiagnosisProtocol.BRASPEN,
        }:
            total = primary_criteria + secondary_criteria
            if total < 2:
                return "sem criterios suficientes", DiagnosisSeverity.NONE
            severity = (
                DiagnosisSeverity.SEVERE
                if severe_marker or total >= 4
                else DiagnosisSeverity.MODERATE
            )
            return "desnutricao", severity

        if protocol == DiagnosisProtocol.SARCOPENIA:
            if primary_criteria >= 1 and secondary_criteria >= 1:
                severity = DiagnosisSeverity.SEVERE if severe_marker else DiagnosisSeverity.MODERATE
                return "sarcopenia provavel/confirmada", severity
            return "sem sarcopenia confirmada", DiagnosisSeverity.NONE

        if protocol == DiagnosisProtocol.CACHEXIA:
            if primary_criteria >= 1 and secondary_criteria >= 2:
                severity = DiagnosisSeverity.SEVERE if severe_marker else DiagnosisSeverity.MODERATE
                return "caquexia provavel", severity
            return "sem criterios suficientes", DiagnosisSeverity.NONE

        if protocol == DiagnosisProtocol.FRAILTY:
            total = primary_criteria + secondary_criteria
            if total >= 3:
                severity = DiagnosisSeverity.SEVERE if severe_marker else DiagnosisSeverity.MODERATE
                return "fragilidade", severity
            if total >= 1:
                return "pre-fragilidade", DiagnosisSeverity.MILD
            return "sem fragilidade", DiagnosisSeverity.NONE

        raise ValueError("Protocolo de diagnostico nao suportado.")

    def build_criteria_text(
        self,
        primary_label: str,
        primary_criteria: int,
        secondary_label: str,
        secondary_criteria: int,
        severe_marker: bool,
    ) -> str:
        marker = "sim" if severe_marker else "nao"
        return (
            f"{primary_label}: {primary_criteria}; "
            f"{secondary_label}: {secondary_criteria}; marcador grave: {marker}"
        )
