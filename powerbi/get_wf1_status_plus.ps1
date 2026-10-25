param(
    [string]$ProjectRoot = "C:\Users\frank\Desktop\WF1\powerbi"
)

$ErrorActionPreference = "Stop"

$SemanticRoot = Join-Path $ProjectRoot "pbi-rep-project.SemanticModel"
$ReportRoot   = Join-Path $ProjectRoot "pbi-rep-project.Report"

$SemanticDefinition = Join-Path $SemanticRoot "definition"
$ReportDefinition   = Join-Path $ReportRoot "definition"
$PagesRoot          = Join-Path $ReportDefinition "pages"

$OutputFile = Join-Path $ProjectRoot "WF1_STATUS_PLUS.txt"


# ============================================================
# HELPERS
# ============================================================

function Write-Section {

    param(
        [string]$Title
    )

    "" | Add-Content $OutputFile

    ("=" * 100) |
        Add-Content $OutputFile

    $Title |
        Add-Content $OutputFile

    ("=" * 100) |
        Add-Content $OutputFile
}


function Write-FileSection {

    param(
        [string]$File
    )

    "" | Add-Content $OutputFile

    ("-" * 100) |
        Add-Content $OutputFile

    "FILE: $File" |
        Add-Content $OutputFile

    ("-" * 100) |
        Add-Content $OutputFile

    Get-Content `
        -LiteralPath $File |
        Add-Content $OutputFile
}


# ============================================================
# HEADER
# ============================================================

"WF1 POWER BI STATUS PLUS" |
    Set-Content $OutputFile

"Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
    Add-Content $OutputFile

"Project: $ProjectRoot" |
    Add-Content $OutputFile


# ============================================================
# ROOT DIRECTORY
# ============================================================

Write-Section "ROOT DIRECTORY"

Get-ChildItem `
    -LiteralPath $ProjectRoot |
    Select-Object `
        Mode,
        LastWriteTime,
        Length,
        Name |
    Format-Table -AutoSize |
    Out-String |
    Add-Content $OutputFile


# ============================================================
# PROJECT TREE
# ============================================================

Write-Section "PROJECT TREE"

cmd /c "tree `"$ProjectRoot`" /F" |
    Add-Content $OutputFile


# ============================================================
# SEMANTIC MODEL SUMMARY
# ============================================================

Write-Section "SEMANTIC MODEL FILES"

if (Test-Path $SemanticDefinition) {

    Get-ChildItem `
        -LiteralPath $SemanticDefinition `
        -Recurse `
        -File |
        Sort-Object FullName |
        ForEach-Object {

            $_.FullName.Substring(
                $ProjectRoot.Length + 1
            ) |
                Add-Content $OutputFile
        }
}


# ============================================================
# RELATIONSHIPS
# ============================================================

Write-Section "RELATIONSHIPS"

$RelationshipsFile =
    Join-Path $SemanticDefinition "relationships.tmdl"

if (Test-Path $RelationshipsFile) {

    Get-Content `
        -LiteralPath $RelationshipsFile |
        Add-Content $OutputFile
}


# ============================================================
# MODEL SETTINGS
# ============================================================

Write-Section "MODEL SETTINGS"

$ModelFile =
    Join-Path $SemanticDefinition "model.tmdl"

if (Test-Path $ModelFile) {

    Get-Content `
        -LiteralPath $ModelFile |
        Add-Content $OutputFile
}


# ============================================================
# MEASURES
# ============================================================

Write-Section "_MEASURES"

$MeasuresFile =
    Join-Path `
        $SemanticDefinition `
        "tables\_Measures.tmdl"

if (Test-Path $MeasuresFile) {

    Get-Content `
        -LiteralPath $MeasuresFile |
        Add-Content $OutputFile

}
else {

    "_Measures.tmdl NOT FOUND" |
        Add-Content $OutputFile
}


# ============================================================
# CORE TABLES
# ============================================================

Write-Section "CORE TABLE DEFINITIONS"

$CoreTables = @(

    "dim_date.tmdl",
    "dim_account.tmdl",
    "dim_kostra_function.tmdl",
    "fact_erp_finance.tmdl",
    "fact_framsikt_finance.tmdl"
)

foreach ($TableFile in $CoreTables) {

    $File =
        Join-Path `
            $SemanticDefinition `
            "tables\$TableFile"

    if (Test-Path $File) {

        Write-FileSection $File
    }
}


# ============================================================
# PAGE SUMMARY
# ============================================================

Write-Section "PAGE SUMMARY"

if (Test-Path $PagesRoot) {

    Get-ChildItem `
        -LiteralPath $PagesRoot `
        -Directory |
        ForEach-Object {

            $PageFile =
                Join-Path `
                    $_.FullName `
                    "page.json"

            if (-not (Test-Path $PageFile)) {
                return
            }

            try {

                $Page =
                    Get-Content `
                        -LiteralPath $PageFile `
                        -Raw |
                    ConvertFrom-Json

                $VisualRoot =
                    Join-Path `
                        $_.FullName `
                        "visuals"

                $VisualCount = 0

                if (Test-Path $VisualRoot) {

                    $VisualCount =
                        @(
                            Get-ChildItem `
                                -LiteralPath $VisualRoot `
                                -Directory
                        ).Count
                }

                "PAGE | $($Page.displayName) | ID=$($Page.name) | Visuals=$VisualCount" |
                    Add-Content $OutputFile

            }
            catch {

                "PAGE ERROR | $PageFile | $($_.Exception.Message)" |
                    Add-Content $OutputFile
            }
        }
}


# ============================================================
# VISUAL SUMMARY
# ============================================================

Write-Section "VISUAL SUMMARY"

$VisualFiles = @()

if (Test-Path $PagesRoot) {

    $VisualFiles =
        @(
            Get-ChildItem `
                -LiteralPath $PagesRoot `
                -Recurse `
                -Filter "visual.json"
        )
}

foreach ($VisualFile in $VisualFiles) {

    try {

        $Visual =
            Get-Content `
                -LiteralPath $VisualFile.FullName `
                -Raw |
            ConvertFrom-Json

        $Relative =
            $VisualFile.FullName.Substring(
                $ProjectRoot.Length + 1
            )

        $Type =
            $Visual.visual.visualType

        $HasQuery =
            $null -ne $Visual.visual.query

        "VISUAL | Type=$Type | Query=$HasQuery | $Relative" |
            Add-Content $OutputFile

    }
    catch {

        "VISUAL JSON ERROR | $($VisualFile.FullName) | $($_.Exception.Message)" |
            Add-Content $OutputFile
    }
}


# ============================================================
# FULL VISUAL JSON
# ============================================================

Write-Section "FULL VISUAL DEFINITIONS"

foreach ($VisualFile in $VisualFiles) {

    Write-FileSection `
        -File $VisualFile.FullName
}


# ============================================================
# MEASURE BINDINGS
# ============================================================

Write-Section "_MEASURES VISUAL BINDINGS"

$MeasureHits =
    $VisualFiles |
    Select-String `
        -Pattern '"Entity"\s*:\s*"_Measures"'

if ($MeasureHits) {

    foreach ($Hit in $MeasureHits) {

        "$($Hit.Path):$($Hit.LineNumber) | $($Hit.Line.Trim())" |
            Add-Content $OutputFile
    }

}
else {

    "No _Measures visual bindings found." |
        Add-Content $OutputFile
}


# ============================================================
# NATIVE QUERY REF
# ============================================================

Write-Section "NATIVE QUERY REF CHECK"

$NativeHits =
    $VisualFiles |
    Select-String `
        -Pattern '"nativeQueryRef"'

if ($NativeHits) {

    foreach ($Hit in $NativeHits) {

        "$($Hit.Path):$($Hit.LineNumber) | $($Hit.Line.Trim())" |
            Add-Content $OutputFile
    }

}
else {

    "No nativeQueryRef entries found." |
        Add-Content $OutputFile
}


# ============================================================
# FORMATTING
# ============================================================

Write-Section "FORMATTING CHECK"

$FormattingPatterns = @(

    '"visualContainerObjects"',
    '"objects"',
    '"dataBars"',
    '"fontColor"',
    '"backgroundColor"',
    '"conditionalFormatting"',
    '"color"'
)

foreach ($Pattern in $FormattingPatterns) {

    "PATTERN: $Pattern" |
        Add-Content $OutputFile

    $Hits =
        $VisualFiles |
        Select-String `
            -Pattern $Pattern

    if ($Hits) {

        foreach ($Hit in $Hits) {

            "$($Hit.Path):$($Hit.LineNumber) | $($Hit.Line.Trim())" |
                Add-Content $OutputFile
        }

    }
    else {

        "  No matches." |
            Add-Content $OutputFile
    }
}


# ============================================================
# DUPLICATE SLICER CHECK
# ============================================================

Write-Section "SLICER SUMMARY"

foreach ($VisualFile in $VisualFiles) {

    try {

        $Visual =
            Get-Content `
                -LiteralPath $VisualFile.FullName `
                -Raw |
            ConvertFrom-Json

        if ($Visual.visual.visualType -ne "slicer") {
            continue
        }

        $Relative =
            $VisualFile.FullName.Substring(
                $ProjectRoot.Length + 1
            )

        $QueryState =
            $Visual.visual.query.queryState

        "SLICER | $Relative" |
            Add-Content $OutputFile

        if ($null -ne $QueryState) {

            $QueryState |
                ConvertTo-Json -Depth 30 |
                Add-Content $OutputFile
        }

    }
    catch {

        "SLICER ERROR | $($VisualFile.FullName)" |
            Add-Content $OutputFile
    }
}


# ============================================================
# JSON VALIDATION
# ============================================================

Write-Section "JSON VALIDATION"

$JsonFailures = @()

foreach ($VisualFile in $VisualFiles) {

    try {

        Get-Content `
            -LiteralPath $VisualFile.FullName `
            -Raw |
        ConvertFrom-Json |
        Out-Null

    }
    catch {

        $JsonFailures +=
            "$($VisualFile.FullName) | $($_.Exception.Message)"
    }
}

if ($JsonFailures.Count -eq 0) {

    "PASS | All visual.json files parse correctly." |
        Add-Content $OutputFile

}
else {

    "FAIL | Invalid JSON found." |
        Add-Content $OutputFile

    $JsonFailures |
        Add-Content $OutputFile
}


# ============================================================
# BACKUP INVENTORY
# ============================================================

Write-Section "BACKUP INVENTORY"

Get-ChildItem `
    -LiteralPath $ProjectRoot `
    -Directory |
    Where-Object {
        $_.Name -like "_backup*"
    } |
    Sort-Object LastWriteTime |
    Select-Object `
        Name,
        LastWriteTime |
    Format-Table -AutoSize |
    Out-String |
    Add-Content $OutputFile


# ============================================================
# FINAL
# ============================================================

Write-Section "END"

"STATUS COMPLETE" |
    Add-Content $OutputFile


Write-Host ""
Write-Host "============================================================"
Write-Host "WF1 STATUS PLUS COMPLETE"
Write-Host "============================================================"
Write-Host ""
Write-Host $OutputFile
Write-Host ""

Get-Item $OutputFile |
    Select-Object `
        FullName,
        Length,
        LastWriteTime