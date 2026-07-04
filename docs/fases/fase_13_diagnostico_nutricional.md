# Fase 13 - Diagnostico Nutricional

## Objetivo

Implementar o modulo de diagnostico nutricional do Nutri Clinic Pro, permitindo registrar classificacoes por protocolos clinicos e manter a confirmacao profissional como etapa obrigatoria de seguranca.

## Entregas

- Tabela `diagnosticos_nutricionais` criada por migration incremental.
- Entidade de dominio `NutritionDiagnosis`.
- Protocolos GLIM, ASPEN, ESPEN, BRASPEN, Sarcopenia, Caquexia e Fragilidade.
- Servico de classificacao com criterios principais/secundarios e marcador de gravidade.
- Repositorio com criacao, listagem, atualizacao, consulta por ID e exclusao logica.
- Tela Desktop substituindo o placeholder de Diagnostico.
- Campos para criterio, classificacao sugerida, gravidade, confirmacao, conduta e observacoes.
- Auditoria para criacao, atualizacao e exclusao logica.

## Validacoes

- Diagnostico exige paciente selecionado.
- Data deve estar no formato ISO `AAAA-MM-DD`.
- Quantidades de criterios nao podem ser negativas.
- A classificacao automatica e apenas sugestiva e pode ser confirmada pela nutricionista.

## Testes

- Classificacao GLIM positiva.
- Classificacao de fragilidade e pre-fragilidade.
- Persistencia, busca, atualizacao, confirmacao e exclusao logica no SQLite migrado.

## Status

Concluida.
