# Fase 14 - Planejamento Alimentar

## Objetivo

Implementar o modulo de planejamento alimentar do Nutri Clinic Pro, permitindo criar planos por paciente, distribuir refeicoes, registrar alimentos e calcular totais nutricionais iniciais.

## Entregas

- Tabelas `planos_alimentares`, `plano_refeicoes` e `plano_itens` criadas por migration incremental.
- Entidades de dominio `MealPlan`, `Meal` e `MealPlanItem`.
- Servico para validar plano/refeicoes/itens, calcular totais e gerar lista de compras.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica em cascata.
- Tela Desktop substituindo o placeholder de Plano Alimentar.
- Cadastro de cabecalho do plano com metas energeticas e de macronutrientes.
- Cadastro de refeicoes, alimentos, quantidades, macros, substituicoes e observacoes.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Plano exige paciente, objetivo e pelo menos uma refeicao.
- Refeicao exige nome e pelo menos um item.
- Item exige alimento, unidade e quantidade maior que zero.
- Valores nutricionais nao podem ser negativos.

## Testes

- Calculo de totais do plano.
- Geracao de lista de compras agrupada.
- Validacao de plano sem refeicao.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.

## Status

Concluida.
