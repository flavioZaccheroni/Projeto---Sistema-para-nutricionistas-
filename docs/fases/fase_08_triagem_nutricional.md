# Fase 8 - Triagem nutricional

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Tela de triagem nutricional substituindo o placeholder.
- Criacao de triagem vinculada a paciente.
- Vinculo opcional com consulta da agenda.
- Protocolos disponiveis: NRS-2002, MUST, MST, SGA/ASG, MNA, MNA-SF, STRONGkids e MIS.
- Calculo automatico de classificacao a partir da pontuacao e protocolo.
- Pesquisa de triagens pelo nome do paciente.
- Listagem de triagens ativas.
- Selecao de triagem para edicao.
- Atualizacao de triagem.
- Exclusao logica.
- Auditoria para criacao, atualizacao e exclusao logica.
- Servico proprio de classificacao de triagens.
- Repositorio proprio para triagens.
- Testes automatizados do servico e do repositorio.

## Regras consideradas nesta fase

- Toda triagem deve estar vinculada a paciente ativo.
- Consulta vinculada e opcional.
- Pontuacao nao pode ser negativa.
- Classificacao e recalculada ao salvar.
- Registros removidos recebem `deleted_at` e deixam de aparecer na listagem.

## Pendencias para fases futuras

- Formularios especificos para cada protocolo.
- Campos estruturados por pergunta.
- Impressao/exportacao da triagem.
- Alertas visuais no dashboard por gravidade.
- Validacao clinica detalhada por faixa etaria e contexto hospitalar.
