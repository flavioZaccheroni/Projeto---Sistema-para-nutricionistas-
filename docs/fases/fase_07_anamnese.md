# Fase 7 - Anamnese

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Tela de anamnese substituindo o placeholder.
- Criacao de anamnese vinculada a paciente.
- Vinculo opcional com consulta da agenda.
- Campos clinicos: queixa principal, HDA, historico patologico, historico familiar, rotina alimentar, comportamento alimentar, sintomas gastrointestinais e observacoes.
- Pesquisa de anamneses pelo nome do paciente.
- Listagem de anamneses ativas.
- Selecao de registro para edicao.
- Atualizacao de anamnese.
- Exclusao logica.
- Auditoria para criacao, atualizacao e exclusao logica.
- Repositorio proprio para anamnese.
- Testes automatizados do fluxo de anamnese.

## Regras consideradas nesta fase

- Toda anamnese deve estar vinculada a um paciente ativo.
- Queixa principal e obrigatoria na interface.
- Consulta vinculada e opcional.
- Registros removidos recebem `deleted_at` e deixam de aparecer na listagem.

## Pendencias para fases futuras

- Formularios especializados por publico clinico.
- Campos estruturados para alergias, aversoes e habitos.
- Questionarios alimentares padronizados.
- Impressao/exportacao da anamnese.
- Historico detalhado de alteracoes por campo.
