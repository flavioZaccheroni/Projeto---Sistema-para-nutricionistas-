# Fluxo Git e GitHub por fase

## Branches

- `main`: versão estável.
- `develop`: integração das fases em andamento.
- `feature/fase-xx-nome`: implementação de cada fase.

## Commit por fase

Use commits pequenos e descritivos:

- `docs: registra arquitetura inicial`
- `feat: cria cadastro de pacientes`
- `test: adiciona testes de antropometria`
- `fix: corrige validacao de data do paciente`

## Publicação no GitHub

Depois de criar um repositório vazio no GitHub, conecte o remoto:

```powershell
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

## Rotina recomendada

```powershell
git checkout -b feature/fase-05-cadastro-pacientes
git status
git add .
git commit -m "feat: implementa cadastro inicial de pacientes"
git push -u origin feature/fase-05-cadastro-pacientes
```
