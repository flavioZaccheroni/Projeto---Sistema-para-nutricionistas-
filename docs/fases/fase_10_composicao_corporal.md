# Fase 10 - Composicao Corporal

## Objetivo

Implementar o modulo de composicao corporal do Nutri Clinic Pro, permitindo registrar avaliacoes por protocolo, vincular a pacientes e consultas, calcular massa gorda e massa magra automaticamente e manter historico auditavel.

## Entregas

- Tabela `composicoes_corporais` criada por migration incremental.
- Permissoes do modulo adicionadas para Administrador, Nutricionista e Auditor.
- Entidade de dominio `BodyComposition` e protocolos principais.
- Servico de calculo para massa gorda e massa magra.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica.
- Tela Desktop integrada ao menu principal.
- Busca por paciente, selecao de consulta vinculada e campos opcionais de bioimpedancia.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Peso deve ser maior que zero.
- Percentual de gordura deve estar entre 0 e 100.
- Data da avaliacao deve usar o formato visual `mm-dd-aaaa`.
- Registro exige paciente selecionado.

## Testes

- Calculo de massa gorda.
- Calculo de massa magra.
- Rejeicao de valores invalidos.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.

## Status

Concluida.
