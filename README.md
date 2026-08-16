# Nutri Clinic Pro

Sistema desktop em Python para atendimento, avaliação e acompanhamento nutricional.

## Situação atual

- Aplicativo desktop em PySide6 com SQLite.
- Arquitetura separada em domínio, serviços, repositórios e interface.
- Migrações versionadas e trilha de auditoria.
- Testes automatizados, lint e workflow de CI.
- Governança clínica com fontes, versões e aprovação profissional.
- Recursos de LGPD para consentimento, portabilidade e anonimização controlada.
- Backup local, checksum e opção criptografada.
- Relatórios em TXT e PDF profissional.
- Evolução gráfica de peso, IMC, gordura corporal, adesão e alertas laboratoriais.

## Requisitos

- Windows com Python 3.12 ou superior.
- Dependências declaradas em `requirements.txt` e `requirements-dev.txt`.

## Preparação do ambiente em D:

O ambiente virtual deve permanecer dentro do próprio projeto. No PowerShell:

```powershell
Set-Location "D:\Projetos\Projeto - sistema nutricionistas"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Se o projeto for movido ou o caminho do Python mudar, recrie ou atualize a `.venv`; não
copie uma `.venv` criada em outro usuário ou computador.

## Execução

### PyCharm

O projeto inclui a configuração compartilhada `Nutri Clinic Pro (.venv)`. Ela utiliza o
interpretador `.venv\Scripts\python.exe`, executa `run_app.py` na raiz do projeto e adiciona
`src` ao `PYTHONPATH`.

Depois de abrir ou recarregar o projeto, selecione `Nutri Clinic Pro (.venv)` no seletor de
execução. Não utilize configurações temporárias chamadas apenas `run_app` ou `__main__`
quando elas exibirem `<No interpreter>`.

```powershell
.\.venv\Scripts\python.exe run_app.py
```

Também é possível instalar o projeto e executar `nutri-app`.

## Primeiro acesso

- E-mail: `admin@local.com`
- Senha inicial: `Nutri1!`

A conta local inicial não exige troca imediata. Senhas novas devem ter pelo menos 7
caracteres, incluindo maiúscula, minúscula, número e símbolo.

## Qualidade

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
```

Os testes de interface usam a plataforma Qt `offscreen` em CI.

## Estrutura

- `src/nutri_app/app`: inicialização e configuração.
- `src/nutri_app/ui`: telas e componentes desktop.
- `src/nutri_app/domain`: entidades e tipos de domínio.
- `src/nutri_app/services`: regras clínicas e serviços de aplicação.
- `src/nutri_app/repositories`: persistência e consultas SQLite.
- `database/migrations`: evolução versionada do banco.
- `docs`: arquitetura, fases, release e implantação.
- `tests`: testes automatizados.

## Segurança e produção

O checklist em `Implantação` bloqueia o status de produção enquanto houver referências
clínicas sem aprovação profissional, ambiente inválido ou controles essenciais ausentes.
Antes de uso real, registre as revisões em `Governança Clínica`, configure backups
criptografados e valide LGPD, restauração e executável em uma máquina limpa.

## Versão

- Produto: Nutri Clinic Pro
- Versão: 1.0.1
- Datas na interface: `dd/mm/aaaa`
