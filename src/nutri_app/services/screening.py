from __future__ import annotations

from nutri_app.domain.screening import ScreeningProtocol


class ScreeningService:
    def classify(self, protocol: ScreeningProtocol, score: float) -> str:
        if score < 0:
            raise ValueError("Pontuacao nao pode ser negativa.")

        if protocol == ScreeningProtocol.NRS_2002:
            return "risco nutricional" if score >= 3 else "sem risco nutricional"
        if protocol == ScreeningProtocol.MUST:
            if score == 0:
                return "baixo risco"
            if score == 1:
                return "medio risco"
            return "alto risco"
        if protocol == ScreeningProtocol.MST:
            return "risco nutricional" if score >= 2 else "sem risco nutricional"
        if protocol == ScreeningProtocol.MNA:
            if score < 17:
                return "desnutricao"
            if score <= 23.5:
                return "risco de desnutricao"
            return "estado nutricional normal"
        if protocol == ScreeningProtocol.MNA_SF:
            if score <= 7:
                return "desnutricao"
            if score <= 11:
                return "risco de desnutricao"
            return "estado nutricional normal"
        if protocol == ScreeningProtocol.STRONGKIDS:
            if score <= 1:
                return "baixo risco"
            if score <= 3:
                return "medio risco"
            return "alto risco"
        if protocol == ScreeningProtocol.MIS:
            if score <= 5:
                return "normal"
            if score <= 10:
                return "desnutricao leve"
            if score <= 20:
                return "desnutricao moderada"
            return "desnutricao grave"
        if protocol == ScreeningProtocol.SGA:
            if score <= 1:
                return "bem nutrido"
            if score == 2:
                return "suspeita ou moderada desnutricao"
            return "desnutricao grave"

        raise ValueError(f"Protocolo nao suportado: {protocol}")

    def is_risk_classification(self, classification: str) -> bool:
        normalized = classification.lower()
        return "risco" in normalized or "desnutricao" in normalized
