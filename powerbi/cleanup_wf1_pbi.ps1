param(
    [string]$ProjectRoot = "C:\Users\frank\Desktop\WF1\powerbi"
)

$ErrorActionPreference = "Stop"

$ReportRoot = Join-Path $ProjectRoot "pbi-rep-project.Report"
$PagesRoot  = Join-Path $ReportRoot "definition\pages"

if (-not (Test-Path -LiteralPath $PagesRoot)) {
    throw "Pages folder not found: $PagesRoot"
}

# Find 00_Control by displayName
$ControlPage = $null
foreach ($dir in @(Get-ChildItem -LiteralPath $PagesRoot -Directory)) {
    $pageFile = Join-Path $dir.FullName "page.json"
    if (-not (Test-Path -LiteralPath $pageFile)) { continue }
    $page = Get-Content -LiteralPath $pageFile -Raw | ConvertFrom-Json
    if ($page.displayName -eq "00_Control") {
        $ControlPage = $dir.FullName
        break
    }
}

if (-not $ControlPage) {
    throw "00_Control page not found."
}

$VisualRoot = Join-Path $ControlPage "visuals"
if (-not (Test-Path -LiteralPath $VisualRoot)) {
    throw "Visuals folder not found for 00_Control."
}

# Backup complete Report folder
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $ProjectRoot "_backup_before_cleanup_$Stamp"
Copy-Item -LiteralPath $ReportRoot -Destination $Backup -Recurse

Write-Host "Backup created: $Backup"
Write-Host "Scanning 00_Control slicers..."

# Group slicers by semantic binding. Keep the first deterministic visual per binding.
$groups = @{}

foreach ($visualDir in @(Get-ChildItem -LiteralPath $VisualRoot -Directory | Sort-Object Name)) {
    $visualFile = Join-Path $visualDir.FullName "visual.json"
    if (-not (Test-Path -LiteralPath $visualFile)) { continue }

    try {
        $v = Get-Content -LiteralPath $visualFile -Raw | ConvertFrom-Json
    }
    catch {
        throw "Invalid JSON before cleanup: $visualFile | $($_.Exception.Message)"
    }

    if ($v.visual.visualType -ne "slicer") { continue }

    $projections = @($v.visual.query.queryState.Values.projections)
    if ($projections.Count -ne 1) {
        Write-Host "SKIP slicer with non-single binding: $($visualDir.Name)"
        continue
    }

    $p = $projections[0]
    $entity = $p.field.Column.Expression.SourceRef.Entity
    $property = $p.field.Column.Property

    if ([string]::IsNullOrWhiteSpace($entity) -or [string]::IsNullOrWhiteSpace($property)) {
        Write-Host "SKIP slicer without column binding: $($visualDir.Name)"
        continue
    }

    $key = "$entity.$property"
    if (-not $groups.ContainsKey($key)) {
        $groups[$key] = New-Object System.Collections.ArrayList
    }
    [void]$groups[$key].Add($visualDir)
}

$removed = New-Object System.Collections.ArrayList
$kept = New-Object System.Collections.ArrayList

foreach ($key in ($groups.Keys | Sort-Object)) {
    $items = @($groups[$key] | Sort-Object Name)
    if ($items.Count -eq 0) { continue }

    $keep = $items[0]
    [void]$kept.Add("$key -> $($keep.Name)")

    if ($items.Count -gt 1) {
        foreach ($dup in $items[1..($items.Count - 1)]) {
            Remove-Item -LiteralPath $dup.FullName -Recurse -Force
            [void]$removed.Add("$key -> $($dup.Name)")
            Write-Host "Removed duplicate: $key | $($dup.Name)"
        }
    }
}

# Validate remaining visual JSON files on 00_Control
$jsonErrors = @()
foreach ($visualFile in @(Get-ChildItem -LiteralPath $VisualRoot -Recurse -Filter "visual.json")) {
    try {
        Get-Content -LiteralPath $visualFile.FullName -Raw | ConvertFrom-Json | Out-Null
    }
    catch {
        $jsonErrors += "$($visualFile.FullName) | $($_.Exception.Message)"
    }
}

if ($jsonErrors.Count -gt 0) {
    Write-Host "JSON validation failed after cleanup. Restore from: $Backup"
    $jsonErrors | ForEach-Object { Write-Host $_ }
    throw "Cleanup produced invalid JSON."
}

# Write audit log outside PBIR definition
$LogFile = Join-Path $ProjectRoot "WF1_CLEANUP_LOG.txt"
"WF1 CLEANUP LOG" | Set-Content $LogFile
"Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $LogFile
"Backup: $Backup" | Add-Content $LogFile
"" | Add-Content $LogFile
"KEPT SLICERS" | Add-Content $LogFile
$kept | Add-Content $LogFile
"" | Add-Content $LogFile
"REMOVED DUPLICATES" | Add-Content $LogFile
if ($removed.Count -eq 0) {
    "None" | Add-Content $LogFile
} else {
    $removed | Add-Content $LogFile
}

Write-Host ""
Write-Host "============================================================"
Write-Host "WF1 cleanup completed successfully"
Write-Host "============================================================"
Write-Host "Removed duplicate slicers: $($removed.Count)"
Write-Host "JSON validation: PASS"
Write-Host "Backup: $Backup"
Write-Host "Audit log: $LogFile"
Write-Host ""
Write-Host "Reopen pbi-rep-project.pbip. Do not save if Power BI reports a validation error."
