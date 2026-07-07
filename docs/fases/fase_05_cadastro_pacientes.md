# Fase 5 - Cadastro de pacientes

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Cadastro de paciente com dados pessoais, contato, convenio, documento, responsavel e historico clinico.
- Listagem de pacientes ativos.
- Pesquisa por nome, telefone, e-mail ou documento.
- Selecao de paciente na tabela para edicao.
- Atualizacao dos dados cadastrais.
- Exclusao logica com preservacao de historico.
- Auditoria para criacao, atualizacao e exclusao logica.
- Testes automatizados para cadastro, pesquisa, edicao e exclusao logica.

## Regras consideradas nesta fase

- Nome completo e obrigatorio.
- Data de nascimento deve usar o formato visual `mm-dd-aaaa`.
- Pacientes removidos recebem `deleted_at` e deixam de aparecer na listagem ativa.
- Historico clinico nao deve ser apagado fisicamente nesta fase.

## Pendencias para fases futuras

- Validacao formal de CPF/documento.
- Cadastro separado de contatos e responsaveis.
- Historico detalhado de alteracoes por campo.
- Importacao/exportacao de cadastro.
- Vinculo com agenda, anamnese e relatorios clinicos completos.
