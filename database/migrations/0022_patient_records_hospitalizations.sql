ALTER TABLE pacientes ADD COLUMN numero_prontuario TEXT;
ALTER TABLE pacientes ADD COLUMN cns TEXT;

CREATE INDEX IF NOT EXISTS idx_pacientes_prontuario
ON pacientes (numero_prontuario);

CREATE INDEX IF NOT EXISTS idx_pacientes_cns
ON pacientes (cns);

CREATE TABLE IF NOT EXISTS internacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    data_admissao TEXT NOT NULL,
    data_alta TEXT,
    unidade TEXT NOT NULL,
    ala TEXT,
    leito TEXT,
    convenio TEXT,
    equipe_responsavel TEXT,
    diagnosticos TEXT,
    condicao_alta TEXT,
    status TEXT NOT NULL DEFAULT 'Ativa',
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE INDEX IF NOT EXISTS idx_internacoes_paciente
ON internacoes (paciente_id, data_admissao DESC);

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('paciente_validar_cpf', '1', 'Valida os digitos verificadores do CPF antes de gravar.'),
    ('paciente_validar_cns', '1', 'Valida o CNS antes de gravar.'),
    ('paciente_unicidade_cpf', '1', 'Impede CPF duplicado entre pacientes ativos.'),
    ('paciente_unicidade_cns', '1', 'Impede CNS duplicado entre pacientes ativos.'),
    ('paciente_unicidade_prontuario', '1', 'Impede numero de prontuario duplicado entre pacientes ativos.');
