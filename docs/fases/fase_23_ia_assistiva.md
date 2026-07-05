# Fase 23 - IA assistiva

## Objetivo

Implementar apoio assistivo inicial para a nutricionista com sugestoes, substituicoes, resumos, interpretacao assistida e alertas inteligentes.

## Entregas

- Tela `IA Assistiva` adicionada ao menu lateral.
- Geracao local baseada em regras, sem dependencia externa.
- Tipos de assistencia:
  - resumo de consulta;
  - sugestoes alimentares;
  - substituicoes;
  - interpretacao assistida;
  - alertas inteligentes.
- Contexto automatico por paciente usando IMC, diagnostico, plano alimentar, exames e adesao.
- Historico das execucoes na tabela `ia_assistente_execucoes`.
- Configuracoes iniciais `ia_modo` e `ia_exige_revisao_profissional`.
- Permissoes do modulo para administrador, nutricionista e auditor.
- Auditoria ao gerar assistencia.

## Validacoes

- Toda resposta inclui aviso de revisao profissional.
- Alertas sao gerados por regras auditaveis.
- Historico preserva entrada, resultado, alertas e status.

## Testes

- Testes de servico para sugestoes e alertas inteligentes.
- Testes de repositorio para contexto clinico e historico de execucoes.
