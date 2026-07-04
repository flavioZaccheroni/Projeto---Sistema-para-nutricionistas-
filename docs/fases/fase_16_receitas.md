# Fase 16 - Receitas

## Objetivo

Implementar o modulo de receitas do Nutri Clinic Pro, permitindo cadastrar ingredientes, modo de preparo, rendimento, foto/caminho e calculo nutricional por porcao e por 100g.

## Entregas

- Tabelas `receitas` e `receita_ingredientes` criadas por migration incremental.
- Permissoes do modulo adicionadas para Administrador, Nutricionista e Auditor.
- Entidades de dominio `Recipe` e `RecipeIngredient`.
- Servico para validar receitas/ingredientes e calcular totais, porcao e 100g.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica em cascata.
- Tela Desktop integrada ao menu principal.
- Cadastro de ingredientes, rendimento, peso total, modo de preparo, foto/caminho e observacoes.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Receita exige nome, rendimento, peso total e pelo menos um ingrediente.
- Ingrediente exige nome, quantidade, unidade e peso em gramas.
- Valores nutricionais nao podem ser negativos.

## Testes

- Calculo de totais da receita.
- Calculo por porcao e por 100g.
- Validacao de receita sem ingredientes.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.

## Status

Concluida.
