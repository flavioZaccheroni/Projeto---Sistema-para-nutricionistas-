CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT,
    rendimento_porcoes REAL NOT NULL,
    peso_total_g REAL NOT NULL,
    modo_preparo TEXT,
    foto_caminho TEXT,
    energia_total_kcal REAL NOT NULL DEFAULT 0,
    proteina_total_g REAL NOT NULL DEFAULT 0,
    carboidrato_total_g REAL NOT NULL DEFAULT 0,
    lipidios_total_g REAL NOT NULL DEFAULT 0,
    fibras_total_g REAL NOT NULL DEFAULT 0,
    sodio_total_mg REAL NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS receita_ingredientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receita_id INTEGER NOT NULL,
    alimento_id INTEGER,
    nome TEXT NOT NULL,
    quantidade REAL NOT NULL,
    unidade TEXT NOT NULL,
    peso_g REAL NOT NULL,
    energia_kcal REAL NOT NULL DEFAULT 0,
    proteina_g REAL NOT NULL DEFAULT 0,
    carboidrato_g REAL NOT NULL DEFAULT 0,
    lipidios_g REAL NOT NULL DEFAULT 0,
    fibras_g REAL NOT NULL DEFAULT 0,
    sodio_mg REAL NOT NULL DEFAULT 0,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (receita_id) REFERENCES receitas(id),
    FOREIGN KEY (alimento_id) REFERENCES alimentos(id)
);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Receitas', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Receitas', 1, 1, 1, 0, 1),
    ('Auditor', 'Receitas', 1, 0, 0, 0, 1);
