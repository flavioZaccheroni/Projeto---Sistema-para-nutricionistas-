CREATE TABLE IF NOT EXISTS paciente_alergias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    alergeno TEXT NOT NULL,
    gravidade TEXT,
    conduta TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE INDEX IF NOT EXISTS idx_paciente_alergias_paciente ON paciente_alergias (paciente_id);

ALTER TABLE alimentos ADD COLUMN alergenos TEXT;
