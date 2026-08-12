from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClinicalValidationReference:
    key: str
    title: str
    reference: str
    population: str
    application_limits: str
    required_review: str = "Revisao e decisao final devem ser feitas pela nutricionista."

    def summary(self) -> str:
        return (
            f"{self.title}. Referencia: {self.reference}. "
            f"Populacao indicada: {self.population}. "
            f"Limites: {self.application_limits}. {self.required_review}"
        )


class ClinicalValidationMatrix:
    _REFERENCES = {
        "NRS-2002": ClinicalValidationReference(
            key="NRS-2002",
            title="Triagem NRS-2002",
            reference="Kondrup et al., 2003; uso hospitalar adulto",
            population="adultos hospitalizados",
            application_limits=(
                "nao substitui avaliacao nutricional completa ou diagnostico de desnutricao"
            ),
        ),
        "MUST": ClinicalValidationReference(
            key="MUST",
            title="Triagem MUST",
            reference="BAPEN MUST",
            population="adultos em comunidade, ambulatorio ou instituicoes",
            application_limits="interpretar junto de perda ponderal, ingestao e condicao clinica",
        ),
        "MST": ClinicalValidationReference(
            key="MST",
            title="Triagem MST",
            reference="Malnutrition Screening Tool",
            population="adultos em triagem rapida",
            application_limits="instrumento de rastreio, sem funcao diagnostica isolada",
        ),
        "MNA": ClinicalValidationReference(
            key="MNA",
            title="Mini Nutritional Assessment",
            reference="MNA full form",
            population="idosos",
            application_limits=(
                "usar com criterio em adultos nao idosos e em condicoes agudas instaveis"
            ),
        ),
        "MNA-SF": ClinicalValidationReference(
            key="MNA-SF",
            title="Mini Nutritional Assessment Short Form",
            reference="MNA-SF",
            population="idosos",
            application_limits="resultado positivo deve direcionar avaliacao nutricional completa",
        ),
        "STRONGkids": ClinicalValidationReference(
            key="STRONGkids",
            title="Triagem STRONGkids",
            reference="STRONGkids pediatric nutritional risk screening",
            population="criancas e adolescentes",
            application_limits="necessita interpretacao pediatrica e acompanhamento de crescimento",
        ),
        "MIS": ClinicalValidationReference(
            key="MIS",
            title="Malnutrition Inflammation Score",
            reference="MIS para pacientes renais",
            population="pacientes com doenca renal, especialmente em dialise",
            application_limits="correlacionar com exames, inflamacao, ingestao e evolucao clinica",
        ),
        "SGA": ClinicalValidationReference(
            key="SGA",
            title="Subjective Global Assessment",
            reference="SGA/ASG",
            population="adultos em avaliacao clinica nutricional",
            application_limits=(
                "depende de entrevista e exame fisico conduzidos por profissional treinada"
            ),
        ),
        "GLIM": ClinicalValidationReference(
            key="GLIM",
            title="Criterios GLIM",
            reference="Global Leadership Initiative on Malnutrition, 2019",
            population="adultos com risco nutricional previamente identificado",
            application_limits=(
                "exige ao menos um criterio fenotipico e um etiologico; "
                "graduar gravidade separadamente"
            ),
        ),
        "ASPEN": ClinicalValidationReference(
            key="ASPEN",
            title="Criterios ASPEN",
            reference="ASPEN/Academy malnutrition characteristics",
            population="adultos em contexto clinico",
            application_limits="requer avaliacao profissional de criterios clinicos e fisicos",
        ),
        "ESPEN": ClinicalValidationReference(
            key="ESPEN",
            title="Criterios ESPEN",
            reference="ESPEN diagnostic criteria for malnutrition",
            population="adultos",
            application_limits=(
                "aplicar junto de IMC, perda ponderal, composicao corporal e contexto clinico"
            ),
        ),
        "BRASPEN": ClinicalValidationReference(
            key="BRASPEN",
            title="Criterios BRASPEN",
            reference="BRASPEN/AMB conforme protocolo adotado pela instituicao",
            population="adultos em contexto clinico brasileiro",
            application_limits=(
                "necessita protocolo institucional atualizado e registro do criterio usado"
            ),
        ),
        "Sarcopenia": ClinicalValidationReference(
            key="Sarcopenia",
            title="Rastreio de sarcopenia",
            reference="EWGSOP2/SARC-F conforme protocolo adotado",
            population="adultos e idosos conforme criterio selecionado",
            application_limits=(
                "confirmar com forca muscular, desempenho e massa muscular quando indicado"
            ),
        ),
        "Caquexia": ClinicalValidationReference(
            key="Caquexia",
            title="Criterios de caquexia",
            reference="consenso clinico aplicavel ao diagnostico de base",
            population="pacientes com doenca cronica/inflamatoria conforme contexto",
            application_limits=(
                "exige avaliacao medica/nutricional integrada e acompanhamento clinico"
            ),
        ),
        "Fragilidade": ClinicalValidationReference(
            key="Fragilidade",
            title="Criterios de fragilidade",
            reference="fenotipo de Fried ou protocolo institucional",
            population="principalmente idosos",
            application_limits=(
                "triagem deve ser integrada a avaliacao funcional e risco nutricional"
            ),
        ),
        "Harris-Benedict": ClinicalValidationReference(
            key="Harris-Benedict",
            title="Equacao Harris-Benedict",
            reference="Harris-Benedict 1919/1984",
            population="adultos; estimativa historica de gasto basal",
            application_limits="pode superestimar em alguns perfis; comparar com contexto clinico",
        ),
        "Mifflin-St. Jeor": ClinicalValidationReference(
            key="Mifflin-St. Jeor",
            title="Equacao Mifflin-St. Jeor",
            reference="Mifflin et al., 1990",
            population="adultos",
            application_limits="estimativa indireta; nao substitui calorimetria quando indicada",
        ),
        "FAO/WHO/UNU": ClinicalValidationReference(
            key="FAO/WHO/UNU",
            title="Equacao FAO/WHO/UNU",
            reference="FAO/WHO/UNU energy requirements",
            population="adultos por faixa etaria e sexo",
            application_limits="ajustar por atividade, injuria e objetivo clinico",
        ),
        "DRI": ClinicalValidationReference(
            key="DRI",
            title="DRI/EER",
            reference="Institute of Medicine Dietary Reference Intakes",
            population="adultos saudaveis ou contextos de referencia",
            application_limits=(
                "usar com cautela em doenca aguda, pacientes criticos e condicoes especiais"
            ),
        ),
        "Owen": ClinicalValidationReference(
            key="Owen",
            title="Equacao Owen",
            reference="Owen resting metabolic rate equations",
            population="adultos",
            application_limits="estimativa por peso; avaliar adequacao ao perfil corporal",
        ),
        "Schofield": ClinicalValidationReference(
            key="Schofield",
            title="Equacao Schofield",
            reference="Schofield predictive equations",
            population="adultos por idade e sexo",
            application_limits="pode variar conforme etnia, composicao corporal e estado clinico",
        ),
        "Cunningham": ClinicalValidationReference(
            key="Cunningham",
            title="Equacao Cunningham",
            reference="Cunningham equation",
            population="adultos com massa magra conhecida",
            application_limits="exige massa magra confiavel; nao usar sem esse dado",
        ),
        "Katch-McArdle": ClinicalValidationReference(
            key="Katch-McArdle",
            title="Equacao Katch-McArdle",
            reference="Katch-McArdle equation",
            population="adultos com percentual de gordura/massa magra conhecido",
            application_limits="dependente da qualidade da avaliacao de composicao corporal",
        ),
    }

    @classmethod
    def get(cls, key: str) -> ClinicalValidationReference:
        try:
            return cls._REFERENCES[key]
        except KeyError as exc:
            raise ValueError(f"Referencia clinica nao cadastrada: {key}") from exc

    @classmethod
    def summary_for(cls, key: str) -> str:
        return cls.get(key).summary()

    @classmethod
    def available_keys(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._REFERENCES))
