$ErrorActionPreference = 'Stop'
$projectDir = Split-Path $PSScriptRoot -Parent
$privateDir = Join-Path $projectDir '.local'
New-Item -ItemType Directory -Force -Path $privateDir | Out-Null
$configPath = Join-Path $privateDir 'dev.env'
if (-not (Test-Path -LiteralPath $configPath)) {
    $dbSecret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
    $appSecret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
    $lines = @("POSTGRES_PASSWORD=$dbSecret", "APP_DB_PASSWORD=$appSecret", "ADMIN_DATABASE_URL=postgres://leadadmin:${dbSecret}@127.0.0.1:55432/leaddesk?sslmode=disable", "DATABASE_URL=postgres://leaddesk:${appSecret}@127.0.0.1:55432/leaddesk?sslmode=disable")
    [IO.File]::WriteAllLines($configPath, $lines)
}
Push-Location $projectDir
try {
    docker compose --env-file .local/dev.env up -d --wait
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL não iniciou.' }
} finally { Pop-Location }
Write-Output 'PostgreSQL local pronto. Credenciais preservadas em app/.local/dev.env.'
