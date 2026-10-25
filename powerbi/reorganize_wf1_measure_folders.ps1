param(
    [string]$ProjectRoot = "C:\Users\frank\Desktop\WF1\powerbi"
)

$ErrorActionPreference = "Stop"
$MeasuresFile = Join-Path $ProjectRoot "pbi-rep-project.SemanticModel\definition\tables\_Measures.tmdl"
if (-not (Test-Path -LiteralPath $MeasuresFile)) { throw "_Measures.tmdl not found: $MeasuresFile" }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = "$MeasuresFile.$stamp.bak"
Copy-Item -LiteralPath $MeasuresFile -Destination $backup

$map = @{
"01 Base\ERP"="01 Financial\ERP\Base"
"01 Base\Framsikt"="01 Financial\Framsikt\Base"
"02 Variance\ERP"="01 Financial\ERP\Variance"
"02 Variance\Framsikt"="01 Financial\Framsikt\Variance"
"03 Status"="04 Status & RAG\Status"
"04 Time Intelligence\Previous"="02 Time Intelligence\ERP\Previous"
"04 Time Intelligence\Change"="02 Time Intelligence\ERP\Change"
"04 Time Intelligence\YTD"="01 Financial\ERP\YTD"
"04 Time Intelligence\Running"="02 Time Intelligence\ERP\Running"
"04 Time Intelligence\Rolling"="02 Time Intelligence\ERP\Rolling"
"05 Context & Totals\Selection"="03 Analysis\Context"
"05 Context & Totals\Benchmark"="03 Analysis\Context"
"05 Context & Totals\Period"="03 Analysis\Context"
"05 Context & Totals\Grand Total"="03 Analysis\Context"
"06 Share & Contribution"="03 Analysis\Contribution"
"07 Ranking"="03 Analysis\Ranking"
"08 Forecast EOY"="05 Forecast & Action\Forecast"
"09 Zero Balance"="05 Forecast & Action\Zero Balance"
"11 Prescription"="05 Forecast & Action\Prescription"
"12 Data Quality\ERP"="06 Data Quality\ERP"
"12 Data Quality\Framsikt"="06 Data Quality\Framsikt"
"12 Data Quality\Status"="06 Data Quality\Status"
"13 RAG\Status"="04 Status & RAG\RAG"
"14 Conditional Formatting\Colors"="07 UI & Formatting\Colors"
"14 Conditional Formatting\Symbols"="07 UI & Formatting\Symbols"
"14 Conditional Formatting\Bars"="07 UI & Formatting\Data Bars"
"15 Selection Context"="07 UI & Formatting\Selection"
"16 Titles & Labels"="07 UI & Formatting\Titles"
"17 Storytelling Commentary"="08 Commentary"
"90 Sandbox"="99 Development\Sandbox"
}

$lines = Get-Content -LiteralPath $MeasuresFile
$changes = 0
$out = foreach ($line in $lines) {
    if ($line -match '^(\s*)displayFolder:\s*(.+?)\s*$') {
        $indent = $Matches[1]
        $old = $Matches[2]
        if ($map.ContainsKey($old)) {
            $changes++
            "$indent`displayFolder: $($map[$old])"
        } else { $line }
    } else { $line }
}

if ($changes -eq 0) { throw "No displayFolder entries were changed. Backup: $backup" }
$out | Set-Content -LiteralPath $MeasuresFile -Encoding utf8

$remaining = Select-String -LiteralPath $MeasuresFile -Pattern 'displayFolder: (01 Base|02 Variance|03 Status|04 Time Intelligence\\YTD|05 Context & Totals|06 Share & Contribution|07 Ranking|08 Forecast EOY|09 Zero Balance|11 Prescription|12 Data Quality|13 RAG|14 Conditional Formatting|15 Selection Context|16 Titles & Labels|17 Storytelling Commentary|90 Sandbox)'

Write-Host ""
Write-Host "WF1 MEASURE FOLDER REORGANIZATION COMPLETE"
Write-Host "Changed displayFolder entries: $changes"
Write-Host "Backup: $backup"
if ($remaining) {
    Write-Host "WARNING: Some old folder paths remain:"
    $remaining | ForEach-Object { Write-Host $_.Line.Trim() }
} else {
    Write-Host "Old folder path validation: PASS"
}
Write-Host ""
Write-Host "Open pbi-rep-project.pbip and verify the _Measures folder tree."
Write-Host "No DAX expressions or measure names were intentionally modified."
