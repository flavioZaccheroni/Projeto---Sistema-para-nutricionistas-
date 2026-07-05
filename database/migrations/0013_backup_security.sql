CREATE TABLE IF NOT EXISTS backups_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caminho_arquivo TEXT NOT NULL,
    tamanho_bytes INTEGER NOT NULL DEFAULT 0,
    checksum_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS configuracoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT NOT NULL UNIQUE,
    valor TEXT NOT NULL,
    descricao TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('backup_diretorio_padrao', 'backups', 'Diretorio padrao para backups locais.'),
    ('senha_tamanho_minimo', '8', 'Tamanho minimo de senha exigido pelo sistema.'),
    ('lgpd_auditoria_ativa', 'true', 'Registro de auditoria para acoes sensiveis.');

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Configuracoes', 1, 1, 1, 1, 1),
    ('Auditor', 'Configuracoes', 1, 0, 0, 0, 1);
