# Fase 4 - Dashboard inicial

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Dashboard com indicadores carregados do banco.
- Total de pacientes ativos.
- Consultas do dia.
- Quantidade de alertas criticos.
- Quantidade de pendencias.
- Tabela de alertas clinicos recentes.
- Tabela de proximas consultas e pendencias.
- Atualizacao manual por botao.
- Atualizacao automatica ao voltar para a tela Dashboard.
- Repositorio proprio para consultas do dashboard.
- Testes automatizados dos indicadores.

## Regras consideradas nesta fase

- Pacientes ativos: registros de `pacientes` sem `deleted_at`.
- Consultas do dia: registros de `consultas` com data igual ao dia atual.
- Alertas criticos: baixo peso em antropometria, triagens com risco e exames com alerta.
- Pendencias: consultas com status pendente, agendada ou confirmada.

## Pendencias para fases futuras

- Graficos de evolucao.
- Semaforo nutricional visual.
- Filtros por periodo, profissional e unidade.
- Alertas clinicos mais completos conforme protocolos avancados.
