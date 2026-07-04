ALTER TABLE relatorios ADD COLUMN titulo TEXT;
ALTER TABLE relatorios ADD COLUMN conteudo TEXT;
ALTER TABLE relatorios ADD COLUMN status TEXT NOT NULL DEFAULT 'Gerado';

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Relatorios', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Relatorios', 1, 1, 1, 0, 1),
    ('Auditor', 'Relatorios', 1, 0, 0, 0, 1);
