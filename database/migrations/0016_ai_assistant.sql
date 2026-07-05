CREATE TABLE IF NOT EXISTS ia_assistente_execucoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    tipo TEXT NOT NULL,
    entrada TEXT,
    resultado TEXT NOT NULL,
    alertas TEXT,
    status TEXT NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('ia_modo', 'assistiva_local', 'Modo inicial de IA baseado em regras locais e auditoria.'),
    ('ia_exige_revisao_profissional', 'true', 'Sugestoes da IA exigem revisao da nutricionista.');

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'IA Assistiva', 1, 1, 1, 1, 1),
    ('Nutricionista', 'IA Assistiva', 1, 1, 1, 0, 1),
    ('Auditor', 'IA Assistiva', 1, 0, 0, 0, 1);
