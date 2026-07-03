# Arquitetura inicial

Este projeto segue a direção do manual: Desktop primeiro, núcleo clínico separado da interface e preparação para API, Web, Mobile e IA.

## Decisão de stack

A implementação inicial usa Python com PySide6, alinhada ao ambiente de desenvolvimento em PyCharm e à recomendação técnica do manual.

## Camadas

- `src/nutri_app/app`: inicialização, configurações e composição da aplicação.
- `src/nutri_app/ui`: telas, componentes visuais e navegação.
- `src/nutri_app/modules`: módulos funcionais separados por domínio clínico.
- `src/nutri_app/domain`: entidades centrais.
- `src/nutri_app/services`: cálculos clínicos e regras reutilizáveis, sem dependência de tela.
- `src/nutri_app/repositories`: persistência e consultas ao banco.
- `database`: schema SQLite inicial e área para migrations futuras.
- `tests`: testes automatizados, começando por cálculos clínicos.

## Módulos do MVP

- Dashboard.
- Usuários e permissões.
- Pacientes.
- Anamnese.
- Antropometria.
- Relatórios.

## Próximas decisões técnicas

- Persistência local: SQLite no MVP.
- Backend/API futura: FastAPI.
- Banco multiusuário futuro: PostgreSQL.
- Relatórios: geração em PDF/Word a partir de templates.
- Segurança: login, perfis, auditoria e LGPD desde a fase inicial.
