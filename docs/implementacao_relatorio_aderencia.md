# Implementacao do Relatorio de Aderencia

Fonte: `Relatorio_Aderencia_Requisitos_Nutri_Clinic_Pro.xlsx`.

Este documento acompanha a implementacao incremental dos requisitos identificados como
parciais ou nao identificados. Um item somente e marcado como concluido quando possui
migracao de banco (quando aplicavel), regra de negocio, interface ou integracao necessaria,
testes automatizados e registro de auditoria para operacoes clinicas relevantes.

## Fase 1 - Prontuario e internacoes

Status: concluida em 2026-08-15.

- `RF-M02-02`: prontuario e episodios de internacao estruturados.
- `RN-M02-01`: validacao e unicidade configuravel de CPF, CNS e prontuario.
- Prontuario automatico no formato `NCP-000000` quando nao informado.
- Internacao com admissao, alta, unidade, ala, leito, convenio, equipe, diagnosticos,
  condicao de alta, status e observacoes.
- Inclusao das internacoes na exportacao de dados do titular (LGPD).
- Auditoria de inclusao, alteracao e exclusao logica de internacoes.

## Proximas fases

1. Avaliacao nutricional central, exame fisico e avaliacao dietetica.
2. Referencias laboratoriais versionadas e correcoes imutaveis.
3. Prescricao nutricional, suplementacao por paciente e evolucao SOAPI.
4. Terapia enteral/parenteral, necessidades e hidratacao.
5. Protocolos clinicos versionados, indicadores e alertas.
6. Seguranca avancada, sessao, segundo fator e escopo por unidade.
7. Homologacao clinica, seguranca, desempenho, instalacao e recuperacao de desastre.
