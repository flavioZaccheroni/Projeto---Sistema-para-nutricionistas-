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
