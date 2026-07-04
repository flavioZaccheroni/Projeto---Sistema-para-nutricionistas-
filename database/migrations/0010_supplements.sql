CREATE TABLE IF NOT EXISTS suplementos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    fabricante TEXT,
    apresentacao TEXT,
    porcao_base REAL NOT NULL DEFAULT 100,
    unidade_porcao TEXT NOT NULL DEFAULT 'ml',
    densidade_calorica REAL,
    osmolaridade_mosm_l REAL,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    fibras_g REAL NOT NULL DEFAULT 0,
    sodio_mg REAL NOT NULL DEFAULT 0,
    composicao TEXT,
    indicacoes TEXT,
    contraindicacoes TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Suplementos', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Suplementos', 1, 1, 1, 0, 1),
    ('Auditor', 'Suplementos', 1, 0, 0, 0, 1);
