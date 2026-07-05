# Fase 24 - Integracoes externas

## Objetivo

Preparar a base para integracoes externas, incluindo APIs futuras, webhooks, app do paciente, financeiro e laboratorios.

## Entregas

- Tela `Integracoes` adicionada ao menu lateral.
- Cadastro de integracoes externas com tipo, endpoint, alias de credencial e observacoes.
- Simulacao de sincronizacao para homologacao local.
- Importacao de exame laboratorial via payload JSON.
- Historico de execucoes com direcao, entidade, status, payload e resultado.
- Tabelas `integracoes_externas` e `integracao_execucoes`.
- Configuracoes iniciais de modo e timeout.
- Permissoes do modulo para administrador, nutricionista e auditor.
- Auditoria ao criar integracao e importar exame.

## Validacoes

- Nome da integracao obrigatorio.
- Endpoint deve iniciar com `http://`, `https://` ou `file://`.
- Payload laboratorial deve ser JSON valido.
- Exame importado exige paciente e itens com nome.

## Testes

- Testes de servico para validacao, simulacao e parser laboratorial.
- Testes de repositorio para cadastro de integracao e historico de execucoes.
