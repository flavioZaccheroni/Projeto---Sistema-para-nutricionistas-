from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class SectionDefinition:
    title: str
    options: tuple[str, ...]
    note_label: str = "Observacoes"


class SelectableSection(QWidget):
    def __init__(self, definition: SectionDefinition) -> None:
        super().__init__()
        self.definition = definition
        self.checkboxes: dict[str, QCheckBox] = {}
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(definition.note_label)
        self.notes.setFixedHeight(58)

        group = QGroupBox(definition.title)
        grid = QGridLayout(group)
        for index, option in enumerate(definition.options):
            checkbox = QCheckBox(option)
            self.checkboxes[option] = checkbox
            grid.addWidget(checkbox, index // 2, index % 2)

        layout = QVBoxLayout(self)
        layout.addWidget(group)
        layout.addWidget(self.notes)

    def clear(self) -> None:
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        self.notes.clear()

    def has_content(self) -> bool:
        return bool(self.selected_options() or self.notes.toPlainText().strip())

    def selected_options(self) -> list[str]:
        return [
            option
            for option, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]

    def to_text(self) -> str:
        selected = "; ".join(self.selected_options()) or "Nenhum"
        lines = [
            f"[{self.definition.title}]",
            f"Selecionados: {selected}",
        ]
        notes = self.notes.toPlainText().strip()
        if notes:
            lines.append(f"{self.definition.note_label}: {notes}")
        return "\n".join(lines)

    def set_text(self, text: str) -> None:
        self.clear()
        cleaned = text.strip()
        if not cleaned:
            return

        selected_text, notes = _extract_selected_and_notes(cleaned, self.definition.note_label)
        selected_items = {
            item.strip()
            for item in selected_text.split(";")
            if item.strip() and item.strip().lower() != "nenhum"
        }
        for option, checkbox in self.checkboxes.items():
            checkbox.setChecked(option in selected_items)
        self.notes.setPlainText(notes)


def serialize_sections(sections: list[SelectableSection]) -> str:
    return "\n\n".join(section.to_text() for section in sections)


def load_sections(sections: list[SelectableSection], text: str) -> None:
    blocks = _split_blocks(text)
    for section in sections:
        section.set_text(blocks.get(section.definition.title, text if len(sections) == 1 else ""))


def summarize_anamnesis_text(text: str) -> str:
    selected_text, notes = _extract_selected_and_notes(text, "Observacoes")
    if selected_text and selected_text.lower() != "nenhum":
        return selected_text
    return notes.replace("\n", " ")[:120]


def _split_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current_title = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_title = stripped[1:-1]
            blocks[current_title] = []
            continue
        if current_title:
            blocks[current_title].append(line)
    return {
        title: "\n".join(lines).strip()
        for title, lines in blocks.items()
    }


def _extract_selected_and_notes(text: str, note_label: str) -> tuple[str, str]:
    selected = ""
    notes: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        if stripped.lower().startswith("selecionados:"):
            selected = stripped.split(":", 1)[1].strip()
            continue
        if stripped.lower().startswith(f"{note_label.lower()}:"):
            notes.append(stripped.split(":", 1)[1].strip())
            continue
        if stripped:
            notes.append(stripped)
    if not selected and notes:
        return "", "\n".join(notes)
    return selected, "\n".join(notes)


QUEIXA_PRINCIPAL = SectionDefinition(
    "Queixa principal",
    (
        "Perda de peso",
        "Ganho de peso",
        "Perda de apetite",
        "Aumento do apetite",
        "Nauseas",
        "Vomitos",
        "Diarreia",
        "Constipacao",
        "Dor abdominal",
        "Distensao abdominal",
        "Disfagia",
        "Odinofagia",
        "Refluxo",
        "Azia",
        "Saciedade precoce",
        "Xerostomia",
        "Alteracao do paladar",
        "Mastigacao prejudicada",
        "Fadiga",
        "Fraqueza",
        "Edema",
        "Hiperglicemia",
        "Hipoglicemia",
        "Desidratacao",
        "Outro",
    ),
    "Campo livre",
)

HISTORIA_DOENCA_ATUAL = SectionDefinition(
    "Historia da doenca atual",
    (
        "Inicio dos sintomas",
        "Tempo de evolucao",
        "Diagnostico principal",
        "Diagnostico secundario",
        "Internacao atual",
        "Internacoes previas",
        "Cirurgia recente",
        "Trauma",
        "Infeccao",
        "Tratamento medicamentoso",
        "Quimioterapia",
        "Radioterapia",
        "Hemodialise",
        "Dialise peritoneal",
        "Ventilacao mecanica",
        "Uso de oxigenio",
    ),
    "Descricao",
)

HISTORICO_PATOLOGICO = SectionDefinition(
    "Historico patologico",
    (
        "Diabetes Mellitus",
        "Hipertensao Arterial",
        "Dislipidemia",
        "Obesidade",
        "Doenca Renal Cronica",
        "Insuficiencia Cardiaca",
        "Doenca Arterial Coronariana",
        "AVC",
        "DPOC",
        "Asma",
        "Doenca Hepatica",
        "Cirrose",
        "Pancreatite",
        "Gastrite",
        "Ulcera peptica",
        "Doenca Inflamatoria Intestinal",
        "Doenca Celiaca",
        "Hipotireoidismo",
        "Hipertireoidismo",
        "Cancer",
        "HIV",
        "Doenca Autoimune",
        "Alergia alimentar",
        "Intolerancia alimentar",
        "Cirurgias previas",
        "Outros",
    ),
)

HISTORICO_FAMILIAR = SectionDefinition(
    "Historico familiar",
    (
        "Diabetes",
        "Hipertensao",
        "Obesidade",
        "Dislipidemia",
        "Infarto",
        "AVC",
        "Doenca Renal",
        "Cancer",
        "Doenca Hepatica",
        "Doenca Autoimune",
        "Doenca da Tireoide",
        "Osteoporose",
        "Sem antecedentes relevantes",
        "Outros",
    ),
)

ROTINA_ALIMENTAR = SectionDefinition(
    "Rotina alimentar",
    (
        "Numero de refeicoes por dia",
        "Horarios regulares",
        "Cafe da manha",
        "Lanche da manha",
        "Almoco",
        "Lanche da tarde",
        "Jantar",
        "Ceia",
        "Consumo de frutas",
        "Consumo de verduras",
        "Consumo de legumes",
        "Consumo de proteinas",
        "Consumo de leite e derivados",
        "Consumo de ultraprocessados",
        "Consumo de frituras",
        "Consumo de doces",
        "Consumo de refrigerantes",
        "Consumo de bebidas alcoolicas",
        "Consumo de cafe",
        "Ingestao hidrica",
        "Uso de suplementos",
        "Uso de fitoterapicos",
    ),
)

COMPORTAMENTO_ALIMENTAR = SectionDefinition(
    "Comportamento alimentar",
    (
        "Apetite preservado",
        "Hiporexia",
        "Hiperfagia",
        "Compulsao alimentar",
        "Belisca entre refeicoes",
        "Alimentacao emocional",
        "Alimentacao noturna",
        "Come rapidamente",
        "Mastiga adequadamente",
        "Mastigacao prejudicada",
        "Come assistindo televisao",
        "Come utilizando celular",
        "Alimenta-se sozinho",
        "Necessita auxilio para alimentacao",
        "Restricao voluntaria de alimentos",
        "Seletividade alimentar",
        "Baixa adesao ao plano alimentar",
    ),
)

SINTOMAS_GASTROINTESTINAIS = SectionDefinition(
    "Sintomas gastrointestinais",
    (
        "Nausea",
        "Vomito",
        "Azia",
        "Refluxo",
        "Eructacao",
        "Flatulencia",
        "Distensao abdominal",
        "Dor abdominal",
        "Diarreia",
        "Constipacao",
        "Fezes endurecidas",
        "Esteatorreia",
        "Sangramento gastrointestinal",
        "Melena",
        "Disfagia",
        "Odinofagia",
        "Saciedade precoce",
        "Intolerancia a lactose",
        "Intolerancia ao gluten",
        "Outros",
    ),
)

OBSERVACOES_CLINICAS = SectionDefinition(
    "Observacoes clinicas",
    (
        "Estado geral preservado",
        "Edema",
        "Ascite",
        "Desidratacao",
        "Sarcopenia",
        "Perda de massa muscular",
        "Perda de gordura subcutanea",
        "Obesidade",
        "Baixo peso",
        "Lesao por pressao",
        "Feridas",
        "Amputacao",
        "Denticao preservada",
        "Protese dentaria",
        "Ausencia dentaria",
        "Xerostomia",
        "Mucosite",
        "Ictericia",
        "Cianose",
        "Palidez",
        "Dependencia para alimentacao",
        "Restricao de mobilidade",
    ),
    "Campo para observacoes",
)

HABITOS_VIDA = [
    SectionDefinition(
        "Atividade fisica",
        ("Sedentario", "Levemente ativo", "Moderadamente ativo", "Muito ativo", "Atleta"),
    ),
    SectionDefinition(
        "Tipo de atividade",
        (
            "Caminhada",
            "Corrida",
            "Musculacao",
            "Ciclismo",
            "Natacao",
            "Pilates",
            "Funcional",
            "Danca",
            "Esportes coletivos",
            "Outro",
        ),
    ),
    SectionDefinition(
        "Frequencia",
        (
            "1 vez/semana",
            "2 vezes/semana",
            "3 vezes/semana",
            "4 vezes/semana",
            "5 vezes/semana",
            "6 vezes/semana",
            "Diariamente",
        ),
    ),
    SectionDefinition("Duracao", ("<30 minutos", "30-60 minutos", "60-90 minutos", "90 minutos")),
    SectionDefinition(
        "Sono",
        (
            "Sono adequado",
            "Insonia",
            "Sono interrompido",
            "Dificuldade para iniciar o sono",
            "Sonolencia diurna",
            "Ronco",
            "Apneia do sono",
            "Usa medicacao para dormir",
            "<5 horas",
            "5-6 horas",
            "7-8 horas",
            "8 horas",
        ),
        "Horas de sono / observacoes",
    ),
    SectionDefinition("Tabagismo", ("Nunca fumou", "Ex-fumante", "Fumante atual", "Fumo passivo")),
    SectionDefinition("Consumo de alcool", ("Nao consome", "Eventual", "Semanal", "Diario")),
    SectionDefinition(
        "Outras substancias",
        ("Cafeina", "Energeticos", "Drogas ilicitas", "Fitoterapicos", "Outro"),
    ),
    SectionDefinition(
        "Hidratacao",
        ("<1 litro/dia", "1-1,5 litros/dia", "1,5-2 litros/dia", "2 litros/dia"),
    ),
    SectionDefinition("Estresse", ("Baixo", "Moderado", "Alto")),
    SectionDefinition(
        "Habitos intestinais",
        (
            "Diario",
            "Dias alternados",
            "3 dias sem evacuar",
            "Diarreia frequente",
            "Uso de laxantes",
        ),
    ),
]

MEDICAMENTOS_SUPLEMENTOS = [
    SectionDefinition(
        "Situacao medicamentosa",
        ("Nao utiliza medicamentos", "Uso continuo", "Uso eventual"),
    ),
    SectionDefinition(
        "Classes de medicamentos",
        (
            "Anti-hipertensivos",
            "Antidiabeticos orais",
            "Insulina",
            "Hipolipemiantes",
            "Diureticos",
            "Corticoides",
            "Anticoagulantes",
            "Antiagregantes plaquetarios",
            "Antidepressivos",
            "Ansioliticos",
            "Antipsicoticos",
            "Anticonvulsivantes",
            "Hormonios tireoidianos",
            "Contraceptivos hormonais",
            "Imunossupressores",
            "Quimioterapicos",
            "Antibioticos",
            "Analgesicos",
            "Anti-inflamatorios",
            "Antiacidos",
            "Inibidores da bomba de protons",
            "Laxantes",
            "Outros",
        ),
    ),
    SectionDefinition(
        "Suplementacao",
        (
            "Whey protein",
            "Creatina",
            "Omega-3",
            "Multivitaminico",
            "Ferro",
            "Calcio",
            "Vitamina D",
            "Vitamina B12",
            "Acido folico",
            "Probioticos",
            "Fibras",
            "Outro",
        ),
    ),
    SectionDefinition("Adesao ao tratamento", ("Boa", "Parcial", "Baixa")),
]

ALERGIAS_INTOLERANCIAS = [
    SectionDefinition(
        "Alergias alimentares",
        (
            "Leite",
            "Ovo",
            "Soja",
            "Trigo",
            "Amendoim",
            "Castanhas",
            "Peixes",
            "Frutos do mar",
            "Gergelim",
            "Milho",
            "Outro",
        ),
    ),
    SectionDefinition(
        "Intolerancias alimentares",
        ("Lactose", "Gluten", "Frutose", "Sorbitol", "Histamina", "Cafeina", "Outro"),
    ),
    SectionDefinition(
        "Alergias medicamentosas",
        (
            "Antibioticos",
            "Anti-inflamatorios",
            "Analgesicos",
            "Anestesicos",
            "Contraste iodado",
            "Latex",
            "Outros",
        ),
    ),
    SectionDefinition(
        "Reacao apresentada",
        (
            "Prurido",
            "Urticaria",
            "Edema",
            "Nauseas",
            "Vomitos",
            "Diarreia",
            "Dispneia",
            "Anafilaxia",
            "Outro",
        ),
    ),
    SectionDefinition("Gravidade", ("Leve", "Moderada", "Grave")),
    SectionDefinition(
        "Conduta",
        (
            "Evita completamente",
            "Consome pequenas quantidades",
            "Em investigacao",
            "Confirmado por exame",
            "Confirmado por teste de provocacao",
            "Autorrelato",
        ),
    ),
]
