# Fase 9 - Antropometria

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Tela de antropometria conectada ao banco.
- Criacao de avaliacao vinculada a paciente.
- Vinculo opcional com consulta da agenda.
- Campos: data, peso, altura, cintura, quadril e observacoes.
- Calculo automatico de IMC.
- Classificacao automatica de IMC adulto.
- Calculo de RCQ.
- Calculo de RCEst.
- Pesquisa de avaliacoes pelo nome do paciente.
- Listagem de avaliacoes ativas.
- Selecao para edicao.
- Atualizacao de avaliacao.
- Exclusao logica.
- Auditoria para criacao, atualizacao e exclusao logica.
- Repositorio proprio para antropometria.
- Testes automatizados do servico e repositorio.

## Regras consideradas nesta fase

- Peso e altura sao obrigatorios e devem ser maiores que zero.
- Cintura e quadril sao opcionais, mas quando preenchidos devem ser maiores que zero.
- RCQ e calculada apenas quando cintura e quadril existem.
- RCEst e calculada quando cintura existe.
- Registros removidos recebem `deleted_at` e deixam de aparecer na listagem.

## Pendencias para fases futuras

- Circunferencias adicionais.
- Dobras cutaneas.
- CMB, AMB e AGB.
- Graficos evolutivos.
- Protocolos por faixa etaria e condicao clinica.
