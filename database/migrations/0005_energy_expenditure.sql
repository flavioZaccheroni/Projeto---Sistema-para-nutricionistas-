CREATE TABLE IF NOT EXISTS gastos_energeticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    consulta_id INTEGER,
    data_avaliacao TEXT NOT NULL,
    sexo TEXT NOT NULL,
    idade_anos INTEGER NOT NULL,
    peso_kg REAL NOT NULL,
    altura_cm REAL NOT NULL,
    massa_magra_kg REAL,
    equacao TEXT NOT NULL,
    fator_atividade REAL NOT NULL,
    fator_estresse REAL NOT NULL,
    ajuste_objetivo_kcal REAL NOT NULL DEFAULT 0,
    tmb_kcal REAL NOT NULL,
    get_kcal REAL NOT NULL,
    proteina_g REAL NOT NULL,
    carboidrato_g REAL NOT NULL,
    lipidios_g REAL NOT NULL,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (consulta_id) REFERENCES consultas(id)
);

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Gasto Energetico', 1, 1, 1, 1, 1),
    ('Nutricionista', 'Gasto Energetico', 1, 1, 1, 0, 1),
    ('Auditor', 'Gasto Energetico', 1, 0, 0, 0, 1);
