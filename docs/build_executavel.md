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

## Instalador Windows

Depois de gerar `dist/Nutri Clinic Pro`, compile `installer/NutriClinicPro.iss` com
Inno Setup 6. O instalador sera criado em `dist/installer`.

Assinatura digital nao pode ser automatizada sem um certificado de code signing.
Quando o certificado estiver disponivel, assine o executavel e o instalador com
`signtool` e registre o hash e a identidade do certificado nas notas da release.
