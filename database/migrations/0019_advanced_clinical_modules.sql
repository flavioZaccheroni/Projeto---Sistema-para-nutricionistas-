CREATE TABLE IF NOT EXISTS registros_clinicos_avancados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modulo TEXT NOT NULL,
    paciente_id INTEGER,
    data_registro TEXT NOT NULL,
    perfil TEXT NOT NULL,
    entradas_json TEXT NOT NULL,
    resultado TEXT NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Anamnese Avancada', 1, 1, 1, 1, 1),
    ('Administrador', 'Exames Avancados', 1, 1, 1, 1, 1),
    ('Administrador', 'Protocolos Clinicos', 1, 1, 1, 1, 1),
    ('Administrador', 'Pediatria', 1, 1, 1, 1, 1),
    ('Administrador', 'Nefrologia', 1, 1, 1, 1, 1),
    ('Administrador', 'Antropometria Avancada', 1, 1, 1, 1, 1),
    ('Administrador', 'Terapia Nutricional', 1, 1, 1, 1, 1),
    ('Administrador', 'Plano Inteligente', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Anamnese Avancada', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Exames Avancados', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Protocolos Clinicos', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Pediatria', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Nefrologia', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Antropometria Avancada', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Terapia Nutricional', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Plano Inteligente', 1, 1, 1, 0, 1),
    ('Auditor', 'Anamnese Avancada', 1, 0, 0, 0, 1),
    ('Auditor', 'Exames Avancados', 1, 0, 0, 0, 1),
    ('Auditor', 'Protocolos Clinicos', 1, 0, 0, 0, 1),
    ('Auditor', 'Pediatria', 1, 0, 0, 0, 1),
    ('Auditor', 'Nefrologia', 1, 0, 0, 0, 1),
    ('Auditor', 'Antropometria Avancada', 1, 0, 0, 0, 1),
    ('Auditor', 'Terapia Nutricional', 1, 0, 0, 0, 1),
    ('Auditor', 'Plano Inteligente', 1, 0, 0, 0, 1);
