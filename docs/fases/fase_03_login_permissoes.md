# Fase 3 - Login e permissoes

## Status

Concluida em nivel de MVP funcional.

## Entregas

- Tela de login antes da janela principal.
- Criacao automatica do usuario administrador inicial.
- Hash de senha com PBKDF2-SHA256 e salt aleatorio.
- Servico de autenticacao com registro de auditoria.
- Repositorio de usuarios.
- Perfis base: Administrador, Nutricionista, Recepcionista e Auditor.
- Permissoes por modulo carregadas via migration.
- Navegacao filtrada conforme permissao de visualizacao do perfil.
- Tela administrativa para criacao de usuarios.
- Testes de senha, login, migrations e repositorios.

## Primeiro acesso

- E-mail: `admin@nutricionistas.local`
- Senha: `Admin@123`

Essa senha deve ser alterada quando a tela de edicao de usuario for implementada.

## Criterios de aceite

- O sistema nao abre a janela principal sem login.
- Senhas nao sao armazenadas em texto puro.
- Tentativas de login sao registradas em auditoria.
- Perfis limitam a navegacao por modulo.
- Administrador consegue criar usuarios iniciais.

## Pendencias para fases futuras

- Tela de edicao e inativacao de usuarios.
- Troca obrigatoria da senha padrao no primeiro acesso.
- Recuperacao de senha.
- Politica configuravel de senha forte.
- Auditoria visual em tela propria.
