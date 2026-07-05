# Fase 21 - Aplicativo do paciente

## Objetivo

Preparar a base do aplicativo do paciente, permitindo que a equipe gerencie acesso, plano publicado, orientacoes e registros de adesao.

## Entregas

- Tela `Aplicativo Paciente` adicionada ao menu lateral.
- Cadastro/atualizacao de acesso do paciente com e-mail e codigo de acesso.
- Publicacao de plano alimentar, orientacao ou mensagem para o paciente.
- Vinculo opcional de publicacao com plano alimentar.
- Registro de adesao com percentual, humor, dificuldades e observacoes.
- Resumo com acessos ativos, publicacoes e adesao media.
- Tabelas `paciente_app_acessos`, `paciente_app_publicacoes` e `paciente_app_adesoes`.
- Permissoes do modulo para administrador, nutricionista e auditor.
- Auditoria de acesso salvo, conteudo publicado e adesao registrada.

## Validacoes

- E-mail de login do paciente deve ser valido.
- Codigo de acesso deve ter pelo menos 6 caracteres.
- Publicacao exige paciente, titulo e conteudo.
- Adesao deve estar entre 0 e 100%.

## Testes

- Testes de servico para codigo de acesso, validacoes e classificacao de adesao.
- Testes de repositorio para acesso, publicacao, adesao e resumo do aplicativo do paciente.
