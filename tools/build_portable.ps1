param(
    [string]$Version = "1.0.1"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$spec = Join-Path $projectRoot "Nutri Clinic Pro.spec"
$appDirectory = Join-Path $projectRoot "dist\Nutri Clinic Pro"
$archive = Join-Path $projectRoot "dist\NutriClinicPro-$Version-Portable-Windows-x64.zip"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Interpretador nao encontrado em $python"
}

Push-Location $projectRoot
try {
    & $python -m PyInstaller --noconfirm --clean $spec
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar o executavel com PyInstaller."
    }

    if (-not (Test-Path -LiteralPath $appDirectory)) {
        throw "Pasta do aplicativo nao foi gerada: $appDirectory"
    }

    Copy-Item `
        -LiteralPath (Join-Path $projectRoot "installer\LEIA-ME_TESTE.txt") `
        -Destination (Join-Path $appDirectory "LEIA-ME_TESTE.txt") `
        -Force

    if (Test-Path -LiteralPath $archive) {
        Remove-Item -LiteralPath $archive -Force
    }
    Compress-Archive -Path (Join-Path $appDirectory "*") -DestinationPath $archive
    Get-Item -LiteralPath $archive | Select-Object FullName, Length, LastWriteTime
    Get-FileHash -LiteralPath $archive -Algorithm SHA256
}
finally {
    Pop-Location
}
