# Nutri Clinic Pro

Projeto iniciado a partir do `Manual_Engenharia_Software_Sistema_Nutricionistas_V1.docx`.

## Objetivo

Construir um MVP Desktop em Python para nutricionistas, preparado para evoluir para API, Web, Mobile, relatórios profissionais e recursos de IA assistiva.

## Stack inicial

- Python 3.12+.
- PySide6 para interface Desktop.
- SQLite no MVP, com caminho preparado para PostgreSQL no futuro.
- Regras clínicas isoladas em serviços testáveis.
- Git/GitHub com commits por fase.

## Estrutura

- `src/nutri_app/app`: inicialização e configurações.
- `src/nutri_app/ui`: telas e componentes Desktop.
- `src/nutri_app/modules`: módulos funcionais por domínio.
- `src/nutri_app/domain`: entidades e regras centrais.
- `src/nutri_app/services`: cálculos clínicos e serviços reutilizáveis.
- `src/nutri_app/repositories`: acesso a dados.
- `database`: schema e banco local.
- `docs`: documentação técnica e fluxo de fases.
- `tests`: testes automatizados.

## Comandos previstos no PyCharm

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:PYTHONPATH="src"
python -m unittest discover -s tests
python -m nutri_app
```

No PyCharm, execute preferencialmente o arquivo `run_app.py` na raiz do projeto.

## Primeiro acesso

- E-mail: `admin@nutricionistas.local`
- Senha: `Admin@123`

## Fases concluídas

- Fase 1: preparação do ambiente.
- Fase 2: arquitetura base.
- Fase 3: login e permissões.
- Fase 4: dashboard inicial.
- Fase 5: cadastro de pacientes.
- Fase 6: agenda.
- Fase 7: anamnese.
- Fase 8: triagem nutricional.
- Fase 9: antropometria.
- Fase 10: composicao corporal.
- Fase 11: gasto energetico.
- Fase 12: exames laboratoriais.
- Fase 13: diagnostico nutricional.
- Fase 14: planejamento alimentar.
- Fase 15: banco de alimentos.
- Fase 16: receitas.
- Fase 17: suplementos.
- Fase 18: relatorios.
- Fase 19: financeiro.
- Fase 20: backup e seguranca.
- Fase 21: aplicativo do paciente.
- Fase 22: portal web.
- Fase 23: IA assistiva.
- Fase 24: integracoes externas.
- Fase 25: testes finais e implantacao.
- Fase 26: anamnese avancada e atendimento adaptativo.
- Fase 27: exames laboratoriais avancados.
- Fase 28: protocolos clinicos BRASPEN/ASPEN/ESPEN e NFPE.
- Fase 29: pediatria.
- Fase 30: nefrologia e hemodialise.
- Fase 31: antropometria avancada integrada ao modulo Antropometria.
- Fase 32: terapia nutricional enteral/parenteral.
- Fase 33: plano alimentar inteligente.

## Versao atual

- Produto: `Nutri Clinic Pro`
- Versao comercial inicial: `1.0.0`
- Status: preparado para empacotamento Windows e validacao comercial.
- Datas na interface: `mm-dd-aaaa`.

## Identidade do app

- Nome: `Nutri Clinic Pro`
- Icone: `icone.png`
