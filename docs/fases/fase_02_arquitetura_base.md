# Fase 2 - Arquitetura base

## Status

Concluida em nivel de fundacao tecnica.

## Entregas

- Composicao da aplicacao por `AppContext`.
- Configuracoes centralizadas em `AppSettings`.
- Migrations SQL versionadas.
- Snapshot de banco em `database/schema.sql`.
- Tema visual centralizado em QSS.
- Navegacao lateral com modulos principais do roadmap.
- Placeholders estruturados para fases futuras.
- Servicos clinicos sem dependencia de interface.
- Testes de calculos, repositorio e migrations.

## Criterios de aceite

- A aplicacao possui camadas separadas para UI, dominio, servicos, repositorios e banco.
- O banco pode ser inicializado de forma idempotente.
- Os testes automatizados passam.
- A arquitetura esta documentada.
- O projeto esta versionado no Git/GitHub.

## Pendencias para fases futuras

- Fase 3: Login, usuarios, perfis e permissoes reais.
- Fase 4: Dashboard com dados reais do banco.
- Fase 5: Cadastro de pacientes completo com edicao, exclusao logica e auditoria.
