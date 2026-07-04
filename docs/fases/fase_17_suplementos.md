# Fase 17 - Suplementos

## Objetivo

Implementar o modulo de suplementos do Nutri Clinic Pro, permitindo cadastrar suplementos orais, formulas enterais e modulos nutricionais com composicao, indicacoes e contraindicacoes.

## Entregas

- Tabela `suplementos` criada por migration incremental.
- Permissoes do modulo adicionadas para Administrador, Nutricionista e Auditor.
- Entidade de dominio `Supplement` e tipos de suplemento/formula/modulo.
- Servico para validacao e calculo proporcional por dose.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica.
- Tela Desktop integrada ao menu principal.
- Campos para fabricante, apresentacao, densidade calorica, osmolaridade, composicao, indicacoes e contraindicacoes.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Nome, porcao base e unidade da porcao sao obrigatorios.
- Porcao base e dose devem ser maiores que zero.
- Densidade calorica, osmolaridade e valores nutricionais nao podem ser negativos.

## Testes

- Calculo proporcional por dose.
- Validacao de suplemento sem nome.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.

## Status

Concluida.
