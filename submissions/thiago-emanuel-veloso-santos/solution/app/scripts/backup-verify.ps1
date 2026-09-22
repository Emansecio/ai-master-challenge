$ErrorActionPreference = 'Stop'
$projectDir = Split-Path $PSScriptRoot -Parent
$backupDir = Join-Path $projectDir '.local/backups'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$restoreDb = "leaddesk_restore_$stamp"
$containerDump = "/tmp/leaddesk-$stamp.dump"
$backupPath = Join-Path $backupDir "leaddesk-$stamp.dump"
$container = 'g4-leaddesk-db-1'
function Invoke-CheckedDocker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw 'Falha na operação de backup/restauração.' }
}
Invoke-CheckedDocker exec $container pg_dump -U leadadmin -d leaddesk -Fc -f $containerDump
Invoke-CheckedDocker cp "${container}:$containerDump" $backupPath
Invoke-CheckedDocker exec $container createdb -U leadadmin $restoreDb
try {
    Invoke-CheckedDocker exec $container pg_restore --exit-on-error -U leadadmin -d $restoreDb $containerDump
    $sql = @'
SELECT json_build_object(
 'opportunities',(SELECT count(*) FROM opportunities),
 'versions',(SELECT count(*) FROM opportunity_versions),
 'classifications',(SELECT count(*) FROM classifications),
 'jobs',(SELECT count(*) FROM jobs),
 'source_records',(SELECT count(*) FROM source_records),
 'data_hash',(SELECT md5(string_agg(doc::text,',' ORDER BY id)) FROM opportunities),
 'classification_hash',(SELECT md5(string_agg(response::text,',' ORDER BY opportunity_id,version,policy_hash)) FROM classifications)
);
'@
    $original = Invoke-CheckedDocker exec $container psql -U leadadmin -d leaddesk -At -c $sql
    $restored = Invoke-CheckedDocker exec $container psql -U leadadmin -d $restoreDb -At -c $sql
    if ($original -ne $restored) { throw 'A restauração não corresponde ao banco de origem. Execute sem gravações concorrentes.' }
    $report = @{ verified = $true; kind = 'logical_pg_dump_restore'; at = (Get-Date).ToString('o'); data = ($restored | ConvertFrom-Json); dump_sha256 = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash; note = 'Restauração local em banco isolado. Não comprova PITR ou alta disponibilidade.' }
    $evidenceDir = Join-Path $projectDir 'evidence'
    New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidenceDir 'backup-restore.json')
    $report | ConvertTo-Json -Depth 5
} finally {
    # O nome é gerado exclusivamente para este teste; a base principal não é alterada.
    if ($restoreDb -notmatch '^leaddesk_restore_[0-9]{14}$') { throw 'Nome inesperado de banco temporário.' }
    Invoke-CheckedDocker exec $container dropdb -U leadadmin $restoreDb
}
