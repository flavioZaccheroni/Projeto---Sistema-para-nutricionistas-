# Fase 11 - Gasto Energetico

## Objetivo

Implementar o modulo de gasto energetico do Nutri Clinic Pro, permitindo calcular TMB/EER, GET e metas iniciais de macronutrientes para apoiar a prescricao nutricional.

## Entregas

- Tabela `gastos_energeticos` criada por migration incremental.
- Permissoes do modulo adicionadas para Administrador, Nutricionista e Auditor.
- Entidade de dominio `EnergyExpenditure`.
- Servico de calculo para Harris-Benedict, Mifflin-St Jeor, Owen, Schofield, FAO/OMS, Cunningham, Katch-McArdle e DRIs.
- Calculo de GET com fator de atividade, fator de estresse e ajuste de objetivo.
- Calculo inicial de proteina, carboidrato e lipidios.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica.
- Tela Desktop integrada ao menu principal antes de Exames.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Idade, peso e altura devem ser maiores que zero.
- Fatores de atividade e estresse devem ser maiores que zero.
- Cunningham e Katch-McArdle exigem massa magra.
- Percentual de lipidios deve estar entre 0 e 99.
- Distribuicao de macros nao pode exceder o GET calculado.

## Testes

- Calculo de TMB por Mifflin-St Jeor.
- Calculo de GET.
- Calculo de macronutrientes.
- Validacao de massa magra obrigatoria para Cunningham.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.

## Status

Concluida.
