# Fase 15 - Banco de Alimentos

## Objetivo

Implementar o banco de alimentos do Nutri Clinic Pro, permitindo cadastrar alimentos TACO, TBCA, regionais, industrializados e personalizados com composicao nutricional e medidas caseiras.

## Entregas

- Tabela `alimentos` criada por migration incremental.
- Permissoes do modulo adicionadas para Administrador, Nutricionista e Auditor.
- Entidade de dominio `Food` e fontes TACO, TBCA, Regional, Industrializado e Personalizado.
- Servico para validacao nutricional e calculo proporcional por porcao.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica.
- Tela Desktop integrada ao menu principal.
- Campos para macronutrientes, fibras, sodio, indice glicemico, micronutrientes e medida caseira.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Nome do alimento e porcao base sao obrigatorios.
- Porcao base deve ser maior que zero.
- Valores nutricionais nao podem ser negativos.
- Indice glicemico nao pode ser negativo quando informado.

## Testes

- Calculo de nutrientes por porcao.
- Validacao de alimento sem nome.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.

## Status

Concluida.
