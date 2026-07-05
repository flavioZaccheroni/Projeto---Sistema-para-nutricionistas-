CREATE TABLE IF NOT EXISTS integracoes_externas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    endpoint TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    credencial_alias TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS integracao_execucoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    integracao_id INTEGER,
    direcao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT,
    resultado TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (integracao_id) REFERENCES integracoes_externas(id)
);

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('integracoes_modo', 'homologacao_local', 'Modo inicial para integracoes externas.'),
    ('integracoes_timeout_segundos', '30', 'Timeout recomendado para APIs externas futuras.');

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Integracoes', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Integracoes', 1, 1, 1, 0, 1),
    ('Auditor', 'Integracoes', 1, 0, 0, 0, 1);
