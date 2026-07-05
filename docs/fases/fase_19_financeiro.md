# Fase 19 - Financeiro

## Objetivo

Controlar atendimentos, pagamentos, recebimentos, inadimplencia e resumo financeiro mensal.

## Entregas

- Tela Financeiro substituindo o placeholder da fase 19.
- Cadastro de lancamentos financeiros de recebimento e pagamento.
- Vinculo opcional com paciente e consulta.
- Controle de categoria, descricao, valor, vencimento, pagamento, forma de pagamento e status.
- Status automatico para aberto, pago, vencido e cancelado.
- Filtros por paciente, periodo e status.
- Resumo mensal com total a receber, recebido, a pagar, pago, vencido e saldo.
- Migration `0012_finance.sql` com tabela `financeiro_lancamentos`.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Descricao obrigatoria.
- Categoria obrigatoria.
- Valor maior que zero.
- Lancamento pago exige data de pagamento.
- Lancamentos vencidos sao classificados conforme data de referencia.

## Testes

- Testes de servico para inadimplencia automatica e validacao.
- Testes de repositorio para criar, listar, atualizar, resumir e excluir lancamentos.
