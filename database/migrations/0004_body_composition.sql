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

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Composicao Corporal', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Composicao Corporal', 1, 1, 1, 0, 1),
    ('Auditor', 'Composicao Corporal', 1, 0, 0, 0, 1);
