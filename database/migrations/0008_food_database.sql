CREATE TABLE IF NOT EXISTS alimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT,
    fonte TEXT NOT NULL,
    porcao_base_g REAL NOT NULL DEFAULT 100,
    medida_caseira TEXT,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    fibras_g REAL NOT NULL DEFAULT 0,
    sodio_mg REAL NOT NULL DEFAULT 0,
    indice_glicemico REAL,
    micronutrientes TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Banco de Alimentos', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Banco de Alimentos', 1, 1, 1, 0, 1),
    ('Auditor', 'Banco de Alimentos', 1, 0, 0, 0, 1);
