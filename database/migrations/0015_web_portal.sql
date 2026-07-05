CREATE TABLE IF NOT EXISTS portal_web_publicacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    caminho_saida TEXT NOT NULL,
    status TEXT NOT NULL,
    total_paginas INTEGER NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('portal_web_diretorio_padrao', 'exports/portal_web', 'Diretorio padrao do portal web estatico.'),
    ('portal_web_nome_publico', 'Nutri Clinic Pro', 'Nome publico exibido no portal web.');

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Portal Web', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Portal Web', 1, 1, 1, 0, 1),
    ('Auditor', 'Portal Web', 1, 0, 0, 0, 1);
