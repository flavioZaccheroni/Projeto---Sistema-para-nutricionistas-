ALTER TABLE usuarios ADD COLUMN troca_senha_obrigatoria INTEGER NOT NULL DEFAULT 1;
ALTER TABLE usuarios ADD COLUMN tentativas_falhas INTEGER NOT NULL DEFAULT 0;
ALTER TABLE usuarios ADD COLUMN bloqueado_ate TEXT;
ALTER TABLE usuarios ADD COLUMN senha_alterada_em TEXT;

ALTER TABLE pacientes ADD COLUMN consentimento_lgpd_em TEXT;
ALTER TABLE pacientes ADD COLUMN retencao_ate TEXT;
ALTER TABLE pacientes ADD COLUMN anonimizado_em TEXT;

CREATE TABLE IF NOT EXISTS referencias_clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modulo TEXT NOT NULL,
    regra TEXT NOT NULL,
    versao TEXT NOT NULL,
    fonte TEXT NOT NULL,
    status_validacao TEXT NOT NULL DEFAULT 'Pendente',
    revisado_por TEXT,
    revisado_em TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (modulo, regra, versao)
);

CREATE TABLE IF NOT EXISTS solicitacoes_privacidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Registrada',
    caminho_exportacao TEXT,
    justificativa TEXT,
    concluida_em TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE IF NOT EXISTS consentimentos_privacidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    versao_politica TEXT NOT NULL,
    concedido INTEGER NOT NULL,
    origem TEXT NOT NULL DEFAULT 'Desktop',
    registrado_por INTEGER,
    registrado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revogado_em TEXT,
    observacoes TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
);

INSERT OR IGNORE INTO referencias_clinicas (modulo, regra, versao, fonte)
VALUES
    ('Triagem Nutricional', 'Classificacao de risco', '1.0', 'Validacao profissional e fonte institucional obrigatorias antes da producao.'),
    ('Composicao Corporal', 'Equacoes corporais', '1.0', 'Validacao por metodo, equipamento e populacao obrigatoria.'),
    ('Gasto Energetico', 'Mifflin e Cunningham', '1.0', 'Documentar publicacao, populacao e limites de aplicacao.'),
    ('Exames', 'Faixas de referencia', '1.0', 'Validar por laboratorio, unidade, sexo biologico, idade e condicao clinica.'),
    ('Diagnostico', 'GLIM e fragilidade', '1.0', 'Versionar diretriz e obter revisao profissional.'),
    ('Suplementos', 'Dose e seguranca', '1.0', 'Validar limites, interacoes e fonte regulatoria.'),
    ('Anamnese Avancada', 'Risco comportamental', '1.0', 'Validar linguagem e criterios com responsavel clinico.'),
    ('Exames Avancados', 'Alertas laboratoriais', '1.0', 'Validar limites e unidades por perfil.'),
    ('Protocolos Clinicos', 'BRASPEN ASPEN ESPEN NFPE', '1.0', 'Registrar versoes oficiais e revisao por especialista.'),
    ('Pediatria', 'IMC percentil e z-score', '1.0', 'Adotar curvas oficiais por idade e sexo.'),
    ('Nefrologia', 'URR e Kt/V', '1.0', 'Validar equacoes, excecoes e metas individualizadas.'),
    ('Antropometria Avancada', 'Indices corporais', '1.0', 'Validar referencias por populacao e metodo.'),
    ('Terapia Nutricional', 'Volume infusao e proteina', '1.0', 'Exigir dupla checagem e protocolo institucional.'),
    ('Plano Inteligente', 'Distribuicao automatica', '1.0', 'Validar metas, restricoes e equivalencias.' );

INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES
    ('seguranca_max_tentativas_login', '5', 'Tentativas consecutivas antes do bloqueio temporario.'),
    ('seguranca_bloqueio_minutos', '15', 'Duracao do bloqueio temporario por falhas de login.'),
    ('seguranca_senha_expira_dias', '90', 'Prazo recomendado para revisao da senha.'),
    ('backup_automatico_ativo', '0', 'Ativa backup automatico na inicializacao quando vencido.'),
    ('backup_intervalo_horas', '24', 'Intervalo minimo entre backups automaticos.'),
    ('backup_retencao_dias', '30', 'Retencao local dos backups automaticos.'),
    ('backup_criptografia_obrigatoria', '1', 'Impede release sem estrategia de criptografia definida.'),
    ('lgpd_politica_versao', '1.0', 'Versao da politica de privacidade e tratamento de dados.'),
    ('lgpd_retencao_padrao_dias', '1825', 'Retencao padrao de prontuario, sujeita a validacao legal.'),
    ('validacao_clinica_obrigatoria', '1', 'Bloqueia release enquanto referencias clinicas estiverem pendentes.');

INSERT OR IGNORE INTO perfis_permissao (
    perfil, modulo, pode_visualizar, pode_criar, pode_editar, pode_excluir, pode_exportar
)
VALUES
    ('Administrador', 'Governanca Clinica', 1, 1, 1, 0, 1),
    ('Nutricionista', 'Governanca Clinica', 1, 0, 1, 0, 1),
    ('Auditor', 'Governanca Clinica', 1, 0, 0, 0, 1);
