CREATE TABLE IF NOT EXISTS implantacao_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    status TEXT NOT NULL,
    detalhes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('versao_produto', '1.0.0', 'Versao comercial inicial apos a fase 25.'),
    ('canal_release', 'desktop_mvp', 'Canal inicial de distribuicao do produto.'),
    ('implantacao_status', 'preparado', 'Status inicial de implantacao apos testes finais.');

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Implantacao', 1, 1, 1, 1, 1),
    ('Auditor', 'Implantacao', 1, 0, 0, 0, 1);
