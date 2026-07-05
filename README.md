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

## Identidade do app

- Nome: `Nutri Clinic Pro`
- Icone: `icone.png`
