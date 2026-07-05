# Build do executavel

Quando chegar a fase de empacotamento, instale as dependencias de build e gere o
executavel Windows com o nome e icone do produto:

```powershell
python -m pip install -r requirements-dev.txt
python -m PyInstaller --noconfirm "Nutri Clinic Pro.spec"
```

Observacoes:

- O app ja usa `icone.png` como icone da janela.
- O executavel gerado pelo PyInstaller tambem deve usar `icone.png`.
- A pasta `dist/Nutri Clinic Pro` sera criada pelo empacotamento.
- Copie a pasta `dist/Nutri Clinic Pro` inteira para testar em outro computador.
