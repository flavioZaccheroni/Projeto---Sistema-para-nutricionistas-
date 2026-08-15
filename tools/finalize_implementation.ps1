param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Message
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$expectedRemote = "https://github.com/flavioZaccheroni/Projeto---Sistema-para-nutricionistas-.git"

function Invoke-Git {
    & git -C $repositoryRoot @args
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar: git $($args -join ' ')"
    }
}

$remote = (& git -C $repositoryRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $remote -ne $expectedRemote) {
    throw "O remoto origin nao corresponde ao repositorio autorizado: $expectedRemote"
}

$python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$ruff = Join-Path $repositoryRoot ".venv\Scripts\ruff.exe"
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $ruff)) {
    throw "Ambiente .venv incompleto. Python e Ruff sao obrigatorios."
}

& $ruff check (Join-Path $repositoryRoot "src") (Join-Path $repositoryRoot "tests")
if ($LASTEXITCODE -ne 0) {
    throw "Ruff encontrou problemas; commit cancelado."
}

& $python -m pytest -q -p no:cacheprovider -c (Join-Path $repositoryRoot "pyproject.toml") `
    (Join-Path $repositoryRoot "tests")
if ($LASTEXITCODE -ne 0) {
    throw "Testes falharam; commit cancelado."
}

Invoke-Git diff --check

$changes = & git -C $repositoryRoot status --porcelain
if (-not $changes) {
    Write-Output "Nenhuma alteracao para versionar."
    exit 0
}

Invoke-Git add -A
$stagedFiles = & git -C $repositoryRoot diff --cached --name-only
$forbiddenPattern = '(^|/)(\.env($|\.)|\.codex_work/)|\.(pem|key|pfx|p12|sqlite|sqlite3|db)$'
$forbiddenFiles = @($stagedFiles | Where-Object { $_ -match $forbiddenPattern })
if ($forbiddenFiles.Count -gt 0) {
    & git -C $repositoryRoot restore --staged -- $forbiddenFiles
    throw "Arquivos potencialmente sensiveis removidos do stage: $($forbiddenFiles -join ', ')"
}

Invoke-Git commit -m $Message
$branch = (& git -C $repositoryRoot branch --show-current).Trim()
if (-not $branch) {
    throw "Nao foi possivel identificar a branch atual."
}
Invoke-Git push origin $branch

$head = (& git -C $repositoryRoot rev-parse HEAD).Trim()
$remoteHead = (& git -C $repositoryRoot rev-parse "origin/$branch").Trim()
if ($head -ne $remoteHead) {
    throw "O commit local nao corresponde a origin/$branch apos o push."
}

Write-Output "Implementacao enviada: $head ($branch) - $Message"
