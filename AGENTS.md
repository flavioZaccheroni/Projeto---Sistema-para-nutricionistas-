# Instrucoes do projeto para agentes

## Commit e push ao concluir implementacoes

O proprietario autorizou que toda implementacao concluida neste projeto seja versionada e
enviada automaticamente ao GitHub.

Ao terminar uma tarefa que altere codigo, banco, testes, instalador ou documentacao do
produto:

1. Execute as validacoes proporcionais a mudanca, incluindo obrigatoriamente Ruff e pytest
   quando houver alteracao em Python.
2. Nao crie commit se uma validacao obrigatoria falhar. Corrija primeiro ou informe o
   bloqueio.
3. Revise o diff e nao inclua credenciais, bancos locais, chaves privadas ou artefatos
   temporarios.
4. Execute `tools/finalize_implementation.ps1` com uma mensagem de commit objetiva.
5. Confirme que `HEAD` e `origin/<branch>` apontam para o mesmo commit.
6. Informe ao usuario o hash e a mensagem do commit enviado.

Repositorio autorizado:
`https://github.com/flavioZaccheroni/Projeto---Sistema-para-nutricionistas-.git`

Excecoes:

- Nao faça commit ou push em tarefas somente de analise, diagnostico ou consulta.
- Respeite quando o usuario pedir explicitamente para nao enviar uma implementacao.
- Nao envie implementacoes incompletas ou com testes falhando sem autorizacao explicita.
