# Fase 22 - Portal Web

## Objetivo

Implantar a base inicial do portal web, preparando a evolucao futura para API e interface web completa.

## Entregas

- Modulo `Portal Web` adicionado ao menu lateral.
- Geracao de portal estatico em `exports/portal_web`.
- Pagina inicial com indicadores operacionais.
- Pagina de agenda com proximas consultas.
- Pagina de publicacoes com conteudos enviados ao aplicativo do paciente.
- CSS proprio do portal em `assets/style.css`.
- Historico de publicacoes na tabela `portal_web_publicacoes`.
- Configuracoes iniciais de diretorio e nome publico do portal.
- Permissoes do modulo para administrador, nutricionista e auditor.
- Auditoria ao gerar o portal.

## Validacoes

- Portal gera tres paginas HTML e arquivo CSS.
- Snapshot busca dados reais do banco local.
- Historico registra titulo, diretorio, status e total de paginas.

## Testes

- Testes de servico para geracao dos arquivos do portal.
- Testes de repositorio para snapshot e historico de publicacao.
