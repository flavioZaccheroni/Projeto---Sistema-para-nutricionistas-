CREATE TABLE IF NOT EXISTS prescricoes_suplementos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    suplemento_id INTEGER NOT NULL,
    suplemento_snapshot_json TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT NOT NULL,
    quantidade REAL NOT NULL,
    unidade TEXT NOT NULL,
    frequencia_dia INTEGER NOT NULL,
    horarios TEXT NOT NULL,
    objetivo TEXT NOT NULL,
    instrucoes TEXT NOT NULL,
    aporte_diario_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Ativa',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (suplemento_id) REFERENCES suplementos(id)
);

CREATE TABLE IF NOT EXISTS acompanhamentos_suplementacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescricao_id INTEGER NOT NULL,
    data_registro TEXT NOT NULL,
    aceitacao INTEGER NOT NULL,
    adesao_percentual REAL NOT NULL,
    intercorrencias TEXT,
    resposta_clinica TEXT,
    motivo_suspensao TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prescricao_id) REFERENCES prescricoes_suplementos(id)
);

CREATE INDEX IF NOT EXISTS idx_prescricoes_suplementos_paciente
ON prescricoes_suplementos (paciente_id, data_inicio DESC);

CREATE INDEX IF NOT EXISTS idx_acompanhamentos_suplementacao_prescricao
ON acompanhamentos_suplementacao (prescricao_id, data_registro DESC);
