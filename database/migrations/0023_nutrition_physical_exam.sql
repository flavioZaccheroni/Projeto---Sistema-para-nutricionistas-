CREATE TABLE IF NOT EXISTS exames_fisicos_nutricionais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    diagnostico_id INTEGER,
    data_avaliacao TEXT NOT NULL,
    achados_json TEXT NOT NULL,
    sinais_sintomas TEXT,
    resumo TEXT NOT NULL,
    gravidade TEXT NOT NULL,
    caminho_imagem TEXT,
    consentimento_imagem INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (diagnostico_id) REFERENCES diagnosticos_nutricionais(id)
);

CREATE INDEX IF NOT EXISTS idx_exames_fisicos_paciente
ON exames_fisicos_nutricionais (paciente_id, data_avaliacao DESC);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Avaliacao Clinica', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Avaliacao Clinica', 1, 1, 1, 0, 1),
    ('Auditor', 'Avaliacao Clinica', 1, 0, 0, 0, 1);
