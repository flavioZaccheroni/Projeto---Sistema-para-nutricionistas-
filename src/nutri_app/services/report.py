from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from nutri_app.domain.patient import Patient


@dataclass(frozen=True)
class ClinicalReportOptions:
    include_anamnesis: bool = True
    include_anthropometry: bool = True
    include_laboratory_exams: bool = True
    include_diagnosis: bool = True
    include_meal_plan: bool = True
    include_energy_expenditure: bool = True
    notes: str = ""

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class GeneratedClinicalReport:
    title: str
    content: str
    parameters: str


class ClinicalReportService:
    def build(
        self,
        patient: Patient,
        options: ClinicalReportOptions,
        context: dict[str, object],
    ) -> GeneratedClinicalReport:
        if patient.id is None:
            raise ValueError("Paciente precisa estar cadastrado para gerar relatorio.")
        if not any(
            [
                options.include_anamnesis,
                options.include_anthropometry,
                options.include_laboratory_exams,
                options.include_diagnosis,
                options.include_meal_plan,
                options.include_energy_expenditure,
            ]
        ):
            raise ValueError("Selecione ao menos uma secao do relatorio.")

        title = f"Relatorio clinico - {patient.name}"
        lines = [
            "Nutri Clinic Pro",
            title,
            f"Gerado em: {date.today().isoformat()}",
            "",
            "Paciente",
            f"- Nome: {patient.name}",
            f"- Data de nascimento: {patient.birth_date.isoformat()}",
            f"- Telefone: {patient.phone or 'Nao informado'}",
            f"- E-mail: {patient.email or 'Nao informado'}",
            f"- Convenio: {patient.health_insurance or 'Nao informado'}",
        ]
        if patient.clinical_notes:
            lines.append(f"- Observacoes clinicas: {patient.clinical_notes}")

        if options.include_anamnesis:
            self._append_anamnesis(lines, context.get("anamnesis"))
        if options.include_anthropometry:
            self._append_anthropometry(lines, context.get("anthropometry"))
        if options.include_energy_expenditure:
            self._append_energy_expenditure(lines, context.get("energy_expenditure"))
        if options.include_laboratory_exams:
            self._append_laboratory_exam(lines, context.get("laboratory_exam"))
        if options.include_diagnosis:
            self._append_diagnosis(lines, context.get("diagnosis"))
        if options.include_meal_plan:
            self._append_meal_plan(lines, context.get("meal_plan"))
        if options.notes.strip():
            lines.extend(["", "Observacoes do relatorio", options.notes.strip()])

        lines.extend(["", "Assinatura do nutricionista:", ""])
        return GeneratedClinicalReport(
            title=title,
            content="\n".join(lines),
            parameters=options.to_json(),
        )

    def export_text(
        self,
        report: GeneratedClinicalReport,
        export_dir: Path,
        patient_name: str,
    ) -> Path:
        export_dir.mkdir(parents=True, exist_ok=True)
        slug = self._slugify(patient_name)
        file_path = export_dir / f"{date.today().isoformat()}_{slug}_relatorio_clinico.txt"
        file_path.write_text(report.content, encoding="utf-8")
        return file_path

    def _append_anamnesis(self, lines: list[str], anamnesis: object) -> None:
        data = self._as_dict(anamnesis)
        lines.extend(["", "Anamnese"])
        if not data:
            lines.append("- Nenhuma anamnese registrada.")
            return
        lines.extend(
            [
                f"- Queixa principal: {data.get('queixa_principal') or 'Nao informado'}",
                f"- Historia atual: {data.get('historia_doenca_atual') or 'Nao informado'}",
                f"- Rotina alimentar: {data.get('rotina_alimentar') or 'Nao informado'}",
                f"- Sintomas GI: {data.get('sintomas_gastrointestinais') or 'Nao informado'}",
            ]
        )

    def _append_anthropometry(self, lines: list[str], anthropometry: object) -> None:
        data = self._as_dict(anthropometry)
        lines.extend(["", "Antropometria"])
        if not data:
            lines.append("- Nenhuma avaliacao antropometrica registrada.")
            return
        lines.extend(
            [
                f"- Data: {data.get('data_avaliacao')}",
                f"- Peso: {data.get('peso_kg')} kg",
                f"- Altura: {data.get('altura_m')} m",
                f"- IMC: {data.get('imc')} ({data.get('classificacao_imc')})",
            ]
        )

    def _append_energy_expenditure(self, lines: list[str], expenditure: object) -> None:
        data = self._as_dict(expenditure)
        lines.extend(["", "Gasto energetico"])
        if not data:
            lines.append("- Nenhum gasto energetico registrado.")
            return
        lines.extend(
            [
                f"- Equacao: {data.get('equacao')}",
                f"- TMB: {data.get('tmb_kcal')} kcal",
                f"- GET: {data.get('get_kcal')} kcal",
                f"- Proteina: {data.get('proteina_g')} g",
                f"- Carboidrato: {data.get('carboidrato_g')} g",
                f"- Lipidios: {data.get('lipidios_g')} g",
            ]
        )

    def _append_laboratory_exam(self, lines: list[str], exam: object) -> None:
        data = self._as_dict(exam)
        lines.extend(["", "Exames laboratoriais"])
        if not data:
            lines.append("- Nenhum exame laboratorial registrado.")
            return
        lines.append(f"- Data: {data.get('data_exame')}")
        lines.append(f"- Laboratorio: {data.get('laboratorio') or 'Nao informado'}")
        for item in data.get("itens", []):
            item_data = self._as_dict(item)
            value = item_data.get("valor")
            unit = item_data.get("unidade") or ""
            alert = item_data.get("alerta") or "Sem alerta"
            lines.append(f"  - {item_data.get('nome')}: {value} {unit} ({alert})")

    def _append_diagnosis(self, lines: list[str], diagnosis: object) -> None:
        data = self._as_dict(diagnosis)
        lines.extend(["", "Diagnostico nutricional"])
        if not data:
            lines.append("- Nenhum diagnostico nutricional registrado.")
            return
        lines.extend(
            [
                f"- Classificacao: {data.get('classificacao')}",
                f"- Gravidade: {data.get('gravidade')}",
                f"- Criterios: {data.get('criterios')}",
                f"- Conduta: {data.get('conduta') or 'Nao informado'}",
            ]
        )

    def _append_meal_plan(self, lines: list[str], plan: object) -> None:
        data = self._as_dict(plan)
        lines.extend(["", "Plano alimentar"])
        if not data:
            lines.append("- Nenhum plano alimentar registrado.")
            return
        lines.extend(
            [
                f"- Objetivo: {data.get('objetivo')}",
                f"- Energia total: {data.get('energia_total_kcal')} kcal",
                f"- Proteina total: {data.get('proteina_total_g')} g",
                f"- Carboidrato total: {data.get('carboidrato_total_g')} g",
                f"- Lipidios totais: {data.get('lipidios_total_g')} g",
            ]
        )
        for meal in data.get("refeicoes", []):
            meal_data = self._as_dict(meal)
            label = meal_data.get("nome")
            time = meal_data.get("horario") or "sem horario"
            lines.append(f"  - {label} ({time})")
            for item in meal_data.get("itens", []):
                item_data = self._as_dict(item)
                lines.append(
                    "    - "
                    f"{item_data.get('alimento')}: "
                    f"{item_data.get('quantidade')} {item_data.get('unidade')}"
                )

    def _as_dict(self, value: object) -> dict:
        return value if isinstance(value, dict) else {}

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
        return slug or "paciente"
