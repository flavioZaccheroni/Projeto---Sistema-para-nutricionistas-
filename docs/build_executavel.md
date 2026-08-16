# Build do executavel

Instale as dependencias de build e gere o pacote portatil Windows com:

```powershell
python -m pip install -r requirements-dev.txt
.\tools\build_portable.ps1
```

Observacoes:

- O app ja usa `icone.png` como icone da janela.
- O executavel gerado pelo PyInstaller tambem deve usar `icone.png`.
- A pasta `dist/Nutri Clinic Pro` sera criada pelo empacotamento.
- O arquivo `dist/NutriClinicPro-1.0.1-Portable-Windows-x64.zip` pode ser copiado
  para outro computador Windows 64 bits.
- Extraia o ZIP inteiro antes de abrir `Nutri Clinic Pro.exe`.
- O banco e os arquivos gerados ficam em `%LOCALAPPDATA%\Nutri Clinic Pro`.
- Bancos locais, relatorios e backups do computador de desenvolvimento nao sao
  incluidos no pacote.

## Teste em outro computador

Use inicialmente `admin@local.com` e `Nutri1!`. O arquivo `LEIA-ME_TESTE.txt`,
incluido no pacote, contem as mesmas instrucoes. Esta versao nao possui assinatura
digital e o Windows SmartScreen pode solicitar uma confirmacao.

## Instalador Windows

Depois de gerar `dist/Nutri Clinic Pro`, compile `installer/NutriClinicPro.iss` com
Inno Setup 6. O instalador sera criado em `dist/installer`.

O Inno Setup 6 precisa estar instalado para gerar o instalador. Assinatura digital
nao pode ser automatizada sem um certificado de code signing.
Quando o certificado estiver disponivel, assine o executavel e o instalador com
`signtool` e registre o hash e a identidade do certificado nas notas da release.
