# Fase 20 - Backup e seguranca

## Objetivo

Implementar recursos iniciais de backup local, verificacao de integridade e painel de seguranca.

## Entregas

- Tela Configuracoes substituindo o placeholder da fase 20.
- Criacao de backup do banco SQLite local.
- Verificacao de backup por checksum SHA-256.
- Historico de backups na tabela `backups_sistema`.
- Tabela `configuracoes` com parametros iniciais de backup e seguranca.
- Painel de seguranca com usuarios ativos, permissoes, hash de senhas, auditoria e checksum.
- Auditoria para criacao e verificacao de backup.
- Protecao no Git para ignorar `backups/` e arquivos temporarios do Word.

## Validacoes

- Backup exige banco local existente.
- Verificacao exige arquivo de backup existente.
- Checksum divergente marca falha e bloqueia validacao.

## Testes

- Testes de servico para criar e verificar backup SQLite.
- Testes de repositorio para salvar historico, atualizar status e contar permissoes.
- Testes de checklist de seguranca.
