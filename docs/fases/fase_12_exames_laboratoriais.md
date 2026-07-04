# Fase 12 - Exames Laboratoriais

## Objetivo

Implementar o modulo de exames laboratoriais do Nutri Clinic Pro, permitindo cadastrar laudos, registrar itens/resultados, comparar valores com referencias e gerar alertas clinicos para acompanhamento.

## Entregas

- Ativacao das tabelas `exames_laboratoriais` e `exame_itens` ja previstas no schema inicial.
- Entidades de dominio `LaboratoryExam` e `LaboratoryExamItem`.
- Servico de apoio para montar referencia e classificar alertas de valores abaixo/acima.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica.
- Tela Desktop substituindo o placeholder de Exames.
- Cadastro de cabecalho do exame com paciente, consulta, data, laboratorio e observacoes.
- Cadastro de itens do exame com valor, unidade, referencia minima/maxima e alerta automatico.
- Integracao dos alertas com o Dashboard ja existente.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Exame exige paciente selecionado.
- Exame exige pelo menos um item.
- Item exige nome.
- Valores e referencias devem ser numericos quando informados.
- Referencia minima nao pode ser maior que a maxima.

## Testes

- Montagem de referencia.
- Classificacao de alerta abaixo/acima da referencia.
- Validacao de nome obrigatorio do item.
- Persistencia, busca, atualizacao e exclusao logica no SQLite migrado.
- Integracao com indicadores e alertas recentes do Dashboard.

## Status

Concluida.
