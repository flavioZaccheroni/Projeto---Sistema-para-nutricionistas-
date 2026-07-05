CREATE TABLE IF NOT EXISTS paciente_app_acessos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL UNIQUE,
    email_login TEXT NOT NULL,
    codigo_acesso TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    ultimo_acesso TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE IF NOT EXISTS paciente_app_publicacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    plano_id INTEGER,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    status TEXT NOT NULL,
    data_publicacao TEXT NOT NULL,
    data_expiracao TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (plano_id) REFERENCES planos_alimentares(id)
);

CREATE TABLE IF NOT EXISTS paciente_app_adesoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    publicacao_id INTEGER,
    data_registro TEXT NOT NULL,
    percentual_adesao REAL NOT NULL,
    humor TEXT,
    dificuldades TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (publicacao_id) REFERENCES paciente_app_publicacoes(id)
);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Aplicativo Paciente', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Aplicativo Paciente', 1, 1, 1, 0, 1),
    ('Auditor', 'Aplicativo Paciente', 1, 0, 0, 0, 1);
