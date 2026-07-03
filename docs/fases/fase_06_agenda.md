# Fase 6 - Agenda

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Tela de agenda substituindo o placeholder da Fase 2.
- Criacao de consulta vinculada ao paciente.
- Tipos de consulta: consulta inicial, retorno, teleconsulta e procedimento.
- Status de consulta: agendada, confirmada, realizada, cancelada e pendente.
- Listagem de consultas com filtros por periodo e status.
- Selecao de consulta para edicao.
- Atualizacao de consulta.
- Acoes rapidas para confirmar, marcar como realizada e cancelar.
- Exclusao logica de consulta.
- Auditoria para criacao, atualizacao, mudanca de status e exclusao logica.
- Repositorio proprio para agenda.
- Testes automatizados do fluxo de agenda.

## Regras consideradas nesta fase

- Toda consulta deve estar vinculada a um paciente ativo.
- Data/hora deve usar o formato `AAAA-MM-DD HH:MM`.
- Consultas removidas recebem `deleted_at` e deixam de aparecer na listagem.
- O dashboard passa a refletir consultas agendadas, confirmadas e pendentes.

## Pendencias para fases futuras

- Visualizacao em calendario semanal/mensal.
- Bloqueios de horario.
- Lembretes e notificacoes.
- Recorrencia de consultas.
- Regras para impedir conflito de horario.
