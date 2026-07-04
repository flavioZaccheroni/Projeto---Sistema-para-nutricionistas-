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
