# Fase 18 - Relatorios

## Objetivo

Implementar a geracao de relatorio clinico simples com historico de arquivos.

## Entregas

- Tela de relatorios substituindo o placeholder inicial.
- Selecao de paciente e secoes clinicas do relatorio.
- Composicao automatica com dados recentes de anamnese, antropometria, exames, diagnostico, gasto energetico e plano alimentar.
- Exportacao em arquivo `.txt` dentro de `exports/relatorios`.
- Historico de relatorios gerados na tabela `relatorios`.
- Auditoria da geracao do relatorio.
- Migration `0011_reports.sql` com campos de titulo, conteudo e status.

## Validacoes

- Paciente obrigatorio para gerar relatorio.
- Ao menos uma secao deve estar selecionada.
- Arquivo exportado com nome padronizado pelo paciente e data.

## Testes

- Testes de servico para geracao de conteudo, exportacao e validacao.
- Testes de repositorio para salvar, listar, carregar historico e montar contexto clinico.
