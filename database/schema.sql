-- Snapshot do schema inicial. A fonte de evolucao sao os arquivos em database/migrations.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS perfis_permissao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil TEXT NOT NULL,
    modulo TEXT NOT NULL,
    pode_visualizar INTEGER NOT NULL DEFAULT 1,
    pode_criar INTEGER NOT NULL DEFAULT 0,
    pode_editar INTEGER NOT NULL DEFAULT 0,
    pode_excluir INTEGER NOT NULL DEFAULT 0,
    pode_exportar INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (perfil, modulo)
);

CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    telefone TEXT,
    email TEXT,
    convenio TEXT,
    documento TEXT,
    responsavel TEXT,
    observacoes_clinicas TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    data_hora TEXT NOT NULL,
    tipo TEXT NOT NULL,
    status TEXT NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE IF NOT EXISTS anamnese (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    queixa_principal TEXT,
    historia_doenca_atual TEXT,
    historico_patologico TEXT,
    historico_familiar TEXT,
    rotina_alimentar TEXT,
    comportamento_alimentar TEXT,
    sintomas_gastrointestinais TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS triagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    protocolo TEXT NOT NULL,
    pontuacao REAL,
    classificacao TEXT NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS antropometrias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_avaliacao TEXT NOT NULL,
    peso_kg REAL NOT NULL,
    altura_m REAL NOT NULL,
    imc REAL NOT NULL,
    classificacao_imc TEXT NOT NULL,
    circunferencia_cintura_cm REAL,
    circunferencia_quadril_cm REAL,
    rcq REAL,
    rcest REAL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS composicoes_corporais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_avaliacao TEXT NOT NULL,
    protocolo TEXT NOT NULL,
    peso_kg REAL NOT NULL,
    percentual_gordura REAL NOT NULL,
    massa_gorda_kg REAL NOT NULL,
    massa_magra_kg REAL NOT NULL,
    agua_corporal_percentual REAL,
    massa_muscular_kg REAL,
    gordura_visceral REAL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS gastos_energeticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_avaliacao TEXT NOT NULL,
    sexo TEXT NOT NULL,
    idade_anos INTEGER NOT NULL,
    peso_kg REAL NOT NULL,
    altura_cm REAL NOT NULL,
    massa_magra_kg REAL,
    equacao TEXT NOT NULL,
    fator_atividade REAL NOT NULL,
    fator_estresse REAL NOT NULL,
    ajuste_objetivo_kcal REAL NOT NULL DEFAULT 0,
    tmb_kcal REAL NOT NULL,
    get_kcal REAL NOT NULL,
    proteina_g REAL NOT NULL,
    carboidrato_g REAL NOT NULL,
    lipidios_g REAL NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS exames_laboratoriais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_exame TEXT NOT NULL,
    laboratorio TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS exame_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exame_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    valor REAL,
    unidade TEXT,
    referencia TEXT,
    alerta TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (exame_id) REFERENCES exames_laboratoriais(id)
);

CREATE TABLE IF NOT EXISTS diagnosticos_nutricionais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_diagnostico TEXT NOT NULL,
    protocolo TEXT NOT NULL,
    criterios TEXT NOT NULL,
    classificacao TEXT NOT NULL,
    gravidade TEXT NOT NULL,
    confirmado INTEGER NOT NULL DEFAULT 0,
    conduta TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS planos_alimentares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_inicio TEXT NOT NULL,
    data_fim TEXT,
    objetivo TEXT NOT NULL,
    energia_alvo_kcal REAL,
    proteina_alvo_g REAL,
    carboidrato_alvo_g REAL,
    lipidios_alvo_g REAL,
    energia_total_kcal REAL NOT NULL DEFAULT 0,
    proteina_total_g REAL NOT NULL DEFAULT 0,
    carboidrato_total_g REAL NOT NULL DEFAULT 0,
    lipidios_total_g REAL NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

CREATE TABLE IF NOT EXISTS plano_refeicoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plano_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    horario TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (plano_id) REFERENCES planos_alimentares(id)
);

CREATE TABLE IF NOT EXISTS plano_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refeicao_id INTEGER NOT NULL,
    alimento TEXT NOT NULL,
    quantidade REAL NOT NULL,
    unidade TEXT NOT NULL,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    substituicoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (refeicao_id) REFERENCES plano_refeicoes(id)
);

CREATE TABLE IF NOT EXISTS alimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT,
    fonte TEXT NOT NULL,
    porcao_base_g REAL NOT NULL DEFAULT 100,
    medida_caseira TEXT,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    fibras_g REAL NOT NULL DEFAULT 0,
    sodio_mg REAL NOT NULL DEFAULT 0,
    indice_glicemico REAL,
    micronutrientes TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT,
    rendimento_porcoes REAL NOT NULL,
    peso_total_g REAL NOT NULL,
    modo_preparo TEXT,
    foto_caminho TEXT,
    energia_total_kcal REAL NOT NULL DEFAULT 0,
    proteina_total_g REAL NOT NULL DEFAULT 0,
    carboidrato_total_g REAL NOT NULL DEFAULT 0,
    lipidios_total_g REAL NOT NULL DEFAULT 0,
    fibras_total_g REAL NOT NULL DEFAULT 0,
    sodio_total_mg REAL NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS receita_ingredientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receita_id INTEGER NOT NULL,
    alimento_id INTEGER,
    nome TEXT NOT NULL,
    quantidade REAL NOT NULL,
    unidade TEXT NOT NULL,
    peso_g REAL NOT NULL,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    fibras_g REAL NOT NULL DEFAULT 0,
    sodio_mg REAL NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (receita_id) REFERENCES receitas(id),
    FOREIGN KEY (alimento_id) REFERENCES alimentos(id)
);

CREATE TABLE IF NOT EXISTS suplementos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    fabricante TEXT,
    apresentacao TEXT,
    porcao_base REAL NOT NULL DEFAULT 100,
    unidade_porcao TEXT NOT NULL DEFAULT 'ml',
    densidade_calorica REAL,
    osmolaridade_mosm_l REAL,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    fibras_g REAL NOT NULL DEFAULT 0,
    sodio_mg REAL NOT NULL DEFAULT 0,
    composicao TEXT,
    indicacoes TEXT,
    contraindicacoes TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS relatorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    tipo TEXT NOT NULL,
    caminho_arquivo TEXT,
    parametros TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE IF NOT EXISTS logs_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    acao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    entidade_id INTEGER,
    detalhes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Dados iniciais aplicados pela migration 0002_seed_permissions.sql:
-- Administrador: acesso completo.
-- Nutricionista: acesso clinico sem exclusao.
-- Recepcionista: acesso operacional.
-- Auditor: acesso de leitura/exportacao.
