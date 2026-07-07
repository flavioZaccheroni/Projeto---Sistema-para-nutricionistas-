from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import log, pi


@dataclass(frozen=True)
class AdvancedModuleDefinition:
    phase: int
    module: str
    title: str
    subtitle: str
    profiles: list[str]
    fields: list[tuple[str, str]]
    evaluator: Callable[[str, dict[str, str], str], str]


class AdvancedClinicalService:
    def definitions(self) -> list[AdvancedModuleDefinition]:
        return [
            AdvancedModuleDefinition(
                26,
                "Anamnese Avancada",
                "Anamnese Avancada",
                "Atendimento adaptativo por perfil clinico, comportamento alimentar e barreiras.",
                [
                    "Emagrecimento",
                    "Hemodialise",
                    "Oncologia",
                    "Pediatria",
                    "Gestacao",
                    "Ambulatorial",
                    "Internacao",
                ],
                [
                    ("pattern", "Padrao alimentar"),
                    ("emotional_triggers", "Gatilhos emocionais"),
                    ("gi_symptoms", "Sintomas gastrointestinais"),
                    ("barriers", "Barreiras percebidas"),
                    ("motivation", "Motivacao 0-10"),
                ],
                self.evaluate_advanced_anamnesis,
            ),
            AdvancedModuleDefinition(
                27,
                "Exames Avancados",
                "Exames Avancados",
                "Interpretacao laboratorial inicial com alertas clinicos prioritarios.",
                ["Adulto", "Idoso", "Gestante", "Pediatria", "Hemodialise", "Oncologia"],
                [
                    ("albumin", "Albumina g/dL"),
                    ("crp", "PCR mg/L"),
                    ("potassium", "Potassio mEq/L"),
                    ("phosphorus", "Fosforo mg/dL"),
                    ("hemoglobin", "Hemoglobina g/dL"),
                    ("hba1c", "HbA1c %"),
                ],
                self.evaluate_advanced_labs,
            ),
            AdvancedModuleDefinition(
                28,
                "Protocolos Clinicos",
                "Protocolos Clinicos",
                "Checklists BRASPEN, ASPEN, ESPEN, NFPE, sarcopenia e fragilidade.",
                ["BRASPEN", "ASPEN", "ESPEN", "NFPE", "Sarcopenia", "Fragilidade"],
                [
                    ("phenotypic", "Criterios fenotipicos"),
                    ("etiologic", "Criterios etiologicos"),
                    ("muscle_loss", "Perda muscular 0-3"),
                    ("fat_loss", "Perda de gordura 0-3"),
                    ("edema", "Edema/ascite 0-3"),
                ],
                self.evaluate_protocols,
            ),
            AdvancedModuleDefinition(
                29,
                "Pediatria",
                "Pediatria",
                "Triagem pediatrica inicial com IMC, percentil informado e alertas por idade.",
                ["Crianca", "Adolescente", "Lactente"],
                [
                    ("age_months", "Idade em meses"),
                    ("weight", "Peso kg"),
                    ("height_cm", "Altura cm"),
                    ("percentile", "Percentil informado"),
                    ("intake", "Ingestao habitual"),
                ],
                self.evaluate_pediatrics,
            ),
            AdvancedModuleDefinition(
                30,
                "Nefrologia",
                "Nefrologia / Hemodialise",
                "Peso seco, ganho interdialitico, URR, Kt/V estimado e alertas renais.",
                ["Hemodialise", "DRC nao dialitica", "Dialise peritoneal"],
                [
                    ("dry_weight", "Peso seco kg"),
                    ("pre_weight", "Peso pre-dialise kg"),
                    ("pre_urea", "Ureia pre mg/dL"),
                    ("post_urea", "Ureia pos mg/dL"),
                    ("session_hours", "Sessao horas"),
                    ("ultrafiltration", "Ultrafiltracao L"),
                ],
                self.evaluate_nephrology,
            ),
            AdvancedModuleDefinition(
                31,
                "Antropometria Avancada",
                "Antropometria Avancada",
                "Indices corporais avancados, circunferencias, CMB, AMB, FMI e FFMI.",
                ["Adulto", "Idoso", "Atleta", "Pediatria"],
                [
                    ("weight", "Peso kg"),
                    ("height_cm", "Altura cm"),
                    ("waist", "Cintura cm"),
                    ("hip", "Quadril cm"),
                    ("arm", "Braco cm"),
                    ("triceps", "Dobra tricipital mm"),
                    ("body_fat", "Gordura corporal %"),
                ],
                self.evaluate_advanced_anthropometry,
            ),
            AdvancedModuleDefinition(
                32,
                "Terapia Nutricional",
                "Terapia Nutricional",
                "Prescricao inicial enteral/parenteral com volume, kcal, proteina e infusao.",
                ["Enteral", "Parenteral", "Suplementacao oral"],
                [
                    ("energy_target", "Meta kcal/dia"),
                    ("protein_target", "Meta proteina g/dia"),
                    ("formula_density", "Densidade kcal/mL"),
                    ("formula_protein", "Proteina g/100mL"),
                    ("infusion_hours", "Horas de infusao"),
                    ("water_flush", "Agua livre mL/dia"),
                ],
                self.evaluate_nutrition_therapy,
            ),
            AdvancedModuleDefinition(
                33,
                "Plano Inteligente",
                "Plano Inteligente",
                "Distribuicao automatica de metas, substituicoes, restricoes e lista de compras.",
                ["Emagrecimento", "Hipertrofia", "Diabetes", "Hemodialise", "DASH", "Mediterranea"],
                [
                    ("energy", "Energia kcal"),
                    ("protein", "Proteina g"),
                    ("carbohydrate", "Carboidrato g"),
                    ("fat", "Lipidios g"),
                    ("meals", "Numero de refeicoes"),
                    ("restrictions", "Restricoes/preferencias"),
                ],
                self.evaluate_smart_meal_plan,
            ),
        ]

    def by_module(self, module: str) -> AdvancedModuleDefinition:
        for definition in self.definitions():
            if definition.module == module:
                return definition
        raise ValueError(f"Modulo avancado nao encontrado: {module}")

    def evaluate_advanced_anamnesis(
        self, profile: str, values: dict[str, str], notes: str
    ) -> str:
        triggers = self._keywords(
            " ".join([values.get("emotional_triggers", ""), values.get("barriers", ""), notes]),
            ["ansiedade", "estresse", "culpa", "compulsao", "restricao", "delivery"],
        )
        motivation = self._float(values.get("motivation"))
        risk = "baixo"
        if len(triggers) >= 3 or motivation < 4:
            risk = "alto"
        elif triggers or motivation < 7:
            risk = "moderado"
        focus = self._adaptive_focus(profile)
        return (
            f"Perfil {profile}. Risco comportamental {risk}. "
            f"Foco sugerido: {focus}. Gatilhos identificados: {', '.join(triggers) or 'nenhum'}."
        )

    def evaluate_advanced_labs(self, profile: str, values: dict[str, str], _notes: str) -> str:
        alerts: list[str] = []
        albumin = self._float(values.get("albumin"))
        crp = self._float(values.get("crp"))
        potassium = self._float(values.get("potassium"))
        phosphorus = self._float(values.get("phosphorus"))
        hemoglobin = self._float(values.get("hemoglobin"))
        hba1c = self._float(values.get("hba1c"))
        if albumin and albumin < 3.5:
            alerts.append("hipoalbuminemia")
        if crp and crp > 10:
            alerts.append("inflamacao")
        if potassium and potassium > 5.5:
            alerts.append("hipercalemia")
        if phosphorus and phosphorus > 4.5:
            alerts.append("hiperfosfatemia")
        if hemoglobin and hemoglobin < 12:
            alerts.append("anemia/risco hematologico")
        if hba1c and hba1c >= 6.5:
            alerts.append("diabetes/descontrole glicemico")
        alert_text = ", ".join(alerts) if alerts else "sem alertas criticos"
        return f"Perfil {profile}. Alertas: {alert_text}."

    def evaluate_protocols(self, profile: str, values: dict[str, str], _notes: str) -> str:
        phenotypic = int(self._float(values.get("phenotypic")))
        etiologic = int(self._float(values.get("etiologic")))
        nfpe = sum(
            int(self._float(values.get(key)))
            for key in ["muscle_loss", "fat_loss", "edema"]
        )
        if profile in {"BRASPEN", "ASPEN", "ESPEN"}:
            if phenotypic >= 2 and etiologic >= 1:
                severity = "grave" if phenotypic + etiologic >= 4 else "moderada"
                return f"{profile}: desnutricao {severity}."
            if phenotypic >= 1 and etiologic >= 1:
                return f"{profile}: desnutricao moderada."
            return f"{profile}: sem criterios suficientes."
        if profile == "NFPE":
            if nfpe >= 6:
                return "NFPE: achados fisicos graves."
            if nfpe >= 3:
                return "NFPE: achados fisicos moderados."
            return "NFPE: sem achados relevantes."
        if profile == "Sarcopenia":
            return "Sarcopenia provavel." if phenotypic >= 1 and nfpe >= 2 else "Sem sarcopenia."
        if profile == "Fragilidade":
            return "Fragilidade." if phenotypic + etiologic + nfpe >= 3 else "Sem fragilidade."
        return "Protocolo avaliado."

    def evaluate_pediatrics(self, profile: str, values: dict[str, str], _notes: str) -> str:
        weight = self._float(values.get("weight"))
        height_m = self._float(values.get("height_cm")) / 100
        percentile = self._float(values.get("percentile"))
        bmi = weight / (height_m * height_m) if weight > 0 and height_m > 0 else 0
        if percentile < 3:
            status = "baixo peso/risco nutricional"
        elif percentile > 97:
            status = "obesidade/risco cardiometabolico"
        elif percentile >= 85:
            status = "sobrepeso"
        else:
            status = "faixa esperada"
        return f"{profile}: IMC {bmi:.1f}, percentil {percentile:g}, classificacao {status}."

    def evaluate_nephrology(self, profile: str, values: dict[str, str], _notes: str) -> str:
        dry_weight = self._float(values.get("dry_weight"))
        pre_weight = self._float(values.get("pre_weight"))
        pre_urea = self._float(values.get("pre_urea"))
        post_urea = self._float(values.get("post_urea"))
        hours = self._float(values.get("session_hours"))
        uf_l = self._float(values.get("ultrafiltration"))
        gain = pre_weight - dry_weight if pre_weight and dry_weight else 0
        urr = ((pre_urea - post_urea) / pre_urea) * 100 if pre_urea > 0 else 0
        ratio = post_urea / pre_urea if pre_urea > 0 else 0
        ktv = -log(max(ratio - 0.008 * hours, 0.01)) + (4 - 3.5 * ratio) * (
            uf_l / dry_weight if dry_weight else 0
        )
        flags = []
        if gain > dry_weight * 0.04:
            flags.append("ganho interdialitico elevado")
        if urr and urr < 65:
            flags.append("URR abaixo da meta")
        if ktv and ktv < 1.2:
            flags.append("Kt/V abaixo da meta")
        return (
            f"{profile}: ganho {gain:.1f} kg, URR {urr:.1f}%, Kt/V {ktv:.2f}. "
            f"Alertas: {', '.join(flags) if flags else 'sem alertas renais principais'}."
        )

    def evaluate_advanced_anthropometry(
        self, profile: str, values: dict[str, str], _notes: str
    ) -> str:
        weight = self._float(values.get("weight"))
        height_m = self._float(values.get("height_cm")) / 100
        waist_m = self._float(values.get("waist")) / 100
        hip_m = self._float(values.get("hip")) / 100
        arm_cm = self._float(values.get("arm"))
        triceps_cm = self._float(values.get("triceps")) / 10
        body_fat = self._float(values.get("body_fat"))
        bmi = weight / height_m**2 if weight and height_m else 0
        conicity = waist_m / (0.109 * (weight / height_m) ** 0.5) if weight and height_m else 0
        bai = (hip_m / (height_m**1.5) - 18) if hip_m and height_m else 0
        fat_mass = weight * body_fat / 100 if body_fat else 0
        fmi = fat_mass / height_m**2 if fat_mass and height_m else 0
        ffmi = (weight - fat_mass) / height_m**2 if weight and height_m else 0
        cmb = arm_cm - (pi * triceps_cm) if arm_cm and triceps_cm else 0
        amb = (cmb**2) / (4 * pi) if cmb else 0
        return (
            f"{profile}: IMC {bmi:.1f}, conicidade {conicity:.2f}, IAC {bai:.1f}, "
            f"FMI {fmi:.1f}, FFMI {ffmi:.1f}, CMB {cmb:.1f} cm, AMB {amb:.1f} cm2."
        )

    def evaluate_nutrition_therapy(
        self, profile: str, values: dict[str, str], _notes: str
    ) -> str:
        energy = self._float(values.get("energy_target"))
        protein = self._float(values.get("protein_target"))
        density = self._float(values.get("formula_density")) or 1
        formula_protein = self._float(values.get("formula_protein"))
        hours = self._float(values.get("infusion_hours")) or 24
        water = self._float(values.get("water_flush"))
        volume_ml = energy / density if density else 0
        infusion = volume_ml / hours if hours else 0
        delivered_protein = volume_ml * formula_protein / 100
        protein_gap = protein - delivered_protein
        return (
            f"{profile}: volume {volume_ml:.0f} mL/dia, infusao {infusion:.0f} mL/h, "
            f"proteina da formula {delivered_protein:.1f} g/dia, "
            f"ajuste proteico {protein_gap:.1f} g, agua livre {water:.0f} mL/dia."
        )

    def evaluate_smart_meal_plan(self, profile: str, values: dict[str, str], _notes: str) -> str:
        energy = self._float(values.get("energy"))
        protein = self._float(values.get("protein"))
        carbs = self._float(values.get("carbohydrate"))
        fat = self._float(values.get("fat"))
        meals = max(int(self._float(values.get("meals"))), 1)
        distribution = [20, 10, 30, 10, 20, 10][:meals]
        if len(distribution) < meals:
            distribution = [round(100 / meals)] * meals
        lines = [
            f"Plano {profile}: {energy:.0f} kcal, P {protein:.0f}g, C {carbs:.0f}g, L {fat:.0f}g.",
            "Distribuicao sugerida:",
        ]
        for index, percentage in enumerate(distribution, 1):
            lines.append(f"Refeicao {index}: {percentage}% = {energy * percentage / 100:.0f} kcal")
        lines.append("Substituicoes: manter equivalencia por grupo alimentar e carboidratos.")
        return "\n".join(lines)

    def _adaptive_focus(self, profile: str) -> str:
        focus = {
            "Hemodialise": "peso seco, potassio, fosforo, adesao hidrica e proteica",
            "Oncologia": "sintomas, inflamacao, caquexia e tolerancia alimentar",
            "Pediatria": "responsaveis, rotina escolar, curva de crescimento e aceitacao",
            "Gestacao": "ganho ponderal, sintomas, suplementacao e seguranca alimentar",
            "Internacao": "risco nutricional, jejum, terapia nutricional e evolucao diaria",
        }
        return focus.get(profile, "padrao alimentar, barreiras, metas e adesao")

    def _keywords(self, text: str, keywords: list[str]) -> list[str]:
        normalized = text.lower()
        return [keyword for keyword in keywords if keyword in normalized]

    def _float(self, value: str | None) -> float:
        try:
            return float((value or "0").replace(",", "."))
        except ValueError:
            return 0.0
