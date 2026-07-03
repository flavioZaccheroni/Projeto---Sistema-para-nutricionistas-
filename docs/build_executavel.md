# Build do executavel

Quando chegar a fase de empacotamento, gere o executavel Windows com o nome e icone do produto:

```powershell
pyinstaller --noconfirm --windowed --name "Nutri Clinic Pro" --icon icone.png run_app.py
```

Observacoes:

- O app ja usa `icone.png` como icone da janela.
- O executavel gerado pelo PyInstaller tambem deve usar `icone.png`.
- A pasta `dist/Nutri Clinic Pro` sera criada pelo empacotamento.
