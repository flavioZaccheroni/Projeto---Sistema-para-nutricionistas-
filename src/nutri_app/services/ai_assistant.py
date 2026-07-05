from __future__ import annotations

from nutri_app.domain.ai_assistant import AIAssistantRequestType, AIAssistantResult


class AIAssistantService:
    disclaimer = "Sugestao assistiva. Revisao e decisao final sao da nutricionista."

    def generate(
        self,
        request_type: AIAssistantRequestType,
        context: dict[str, object],
        prompt: str = "",
    ) -> AIAssistantResult:
        if request_type == AIAssistantRequestType.CONSULTATION_SUMMARY:
            return self._summary(context, prompt)
        if request_type == AIAssistantRequestType.FOOD_SUGGESTIONS:
            return self._food_suggestions(context, prompt)
        if request_type == AIAssistantRequestType.SUBSTITUTIONS:
            return self._substitutions(context, prompt)
        if request_type == AIAssistantRequestType.ASSISTED_INTERPRETATION:
            return self._interpretation(context, prompt)
        return self._smart_alerts(context, prompt)

    def _summary(self, context: dict[str, object], prompt: str) -> AIAssistantResult:
        patient = self._value(context, "patient_name", "Paciente nao informado")
        bmi = self._value(context, "bmi", "sem IMC recente")
        diagnosis = self._value(context, "diagnosis", "sem diagnostico recente")
        plan = self._value(context, "meal_plan_objective", "sem plano publicado")
        adherence = self._value(context, "average_adherence", "sem adesao registrada")
        result = (
            f"{self.disclaimer}\n\n"
            f"Resumo: {patient} apresenta IMC {bmi}, diagnostico {diagnosis}, "
            f"objetivo alimentar {plan} e adesao media {adherence}%. "
            f"Pontos informados pela profissional: {prompt or 'nenhum ponto adicional.'}"
        )
        return AIAssistantResult(AIAssistantRequestType.CONSULTATION_SUMMARY, result)

    def _food_suggestions(self, context: dict[str, object], prompt: str) -> AIAssistantResult:
        objective = str(self._value(context, "meal_plan_objective", "")).lower()
        suggestions = [
            "Priorizar alimentos in natura e minimamente processados.",
            "Distribuir proteina ao longo das principais refeicoes.",
            "Incluir fibras por vegetais, frutas e leguminosas conforme tolerancia.",
        ]
        if "perda" in objective or "emagrec" in objective:
            suggestions.append(
                "Reforcar saciedade com vegetais, proteinas magras e planejamento de lanches."
            )
        if "ganho" in objective or "hipertrof" in objective:
            suggestions.append("Avaliar aumento gradual de energia e proteina conforme evolucao.")
        result = self.disclaimer + "\n\n" + "\n".join(f"- {item}" for item in suggestions)
        if prompt:
            result += f"\n- Observacao considerada: {prompt}"
        return AIAssistantResult(AIAssistantRequestType.FOOD_SUGGESTIONS, result)

    def _substitutions(self, context: dict[str, object], prompt: str) -> AIAssistantResult:
        result = (
            f"{self.disclaimer}\n\n"
            "- Arroz pode ser alternado com batata, mandioca, quinoa ou macarrao simples.\n"
            "- Frango pode ser alternado com ovos, peixe, carne magra ou leguminosas.\n"
            "- Leite pode ser alternado com iogurte natural ou bebida sem acucar, "
            "conforme tolerancia.\n"
            "- Lanches podem usar fruta, castanhas, iogurte ou sanduiche simples."
        )
        if prompt:
            result += f"\n- Preferencia/restricao registrada: {prompt}"
        return AIAssistantResult(AIAssistantRequestType.SUBSTITUTIONS, result)

    def _interpretation(self, context: dict[str, object], prompt: str) -> AIAssistantResult:
        alerts = self._build_alerts(context)
        result = (
            f"{self.disclaimer}\n\n"
            "Interpretacao assistida:\n"
            f"- IMC recente: {self._value(context, 'bmi', 'nao informado')}.\n"
            f"- Diagnostico: {self._value(context, 'diagnosis', 'nao informado')}.\n"
            f"- Alertas laboratoriais: {self._value(context, 'lab_alerts', 0)}.\n"
            f"- Observacao profissional: {prompt or 'sem observacao adicional.'}"
        )
        return AIAssistantResult(
            AIAssistantRequestType.ASSISTED_INTERPRETATION,
            result,
            alerts,
        )

    def _smart_alerts(self, context: dict[str, object], prompt: str) -> AIAssistantResult:
        alerts = self._build_alerts(context)
        if not alerts:
            alerts = ["Nenhum alerta inteligente gerado com os dados atuais."]
        result = self.disclaimer + "\n\n" + "\n".join(f"- {alert}" for alert in alerts)
        if prompt:
            result += f"\n- Contexto adicional: {prompt}"
        return AIAssistantResult(AIAssistantRequestType.SMART_ALERTS, result, alerts)

    def _build_alerts(self, context: dict[str, object]) -> list[str]:
        alerts: list[str] = []
        bmi = self._optional_float(context.get("bmi"))
        lab_alerts = int(context.get("lab_alerts") or 0)
        adherence = self._optional_float(context.get("average_adherence"))
        if bmi is not None and bmi < 18.5:
            alerts.append("IMC abaixo de 18,5: revisar risco nutricional e conduta.")
        if lab_alerts > 0:
            alerts.append(f"Existem {lab_alerts} alerta(s) laboratorial(is) para revisar.")
        if adherence is not None and adherence < 60:
            alerts.append("Adesao abaixo de 60%: investigar barreiras e simplificar plano.")
        return alerts

    def _value(self, context: dict[str, object], key: str, default: object) -> object:
        value = context.get(key)
        return value if value not in [None, ""] else default

    def _optional_float(self, value: object) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
