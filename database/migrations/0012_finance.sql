CREATE TABLE IF NOT EXISTS financeiro_lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    consulta_id INTEGER,
    tipo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    data_vencimento TEXT NOT NULL,
    data_pagamento TEXT,
    forma_pagamento TEXT,
    status TEXT NOT NULL,
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
    ('Administrador', 'Financeiro', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Financeiro', 1, 1, 1, 0, 1),
    ('Recepcionista', 'Financeiro', 1, 1, 1, 0, 0),
    ('Auditor', 'Financeiro', 1, 0, 0, 0, 1);
