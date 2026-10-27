param(
    [string]$ProjectRoot = "C:\Users\frank\Desktop\WF1"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================"
Write-Host "WF1 POWER BI REPORT STATUS"
Write-Host "============================================================"
Write-Host ""

Write-Host "Project root:"
Write-Host $ProjectRoot
Write-Host ""


# ============================================================
# PROJECT CHECK
# ============================================================

if (-not (Test-Path $ProjectRoot)) {

    Write-Host "PROJECT NOT FOUND" -ForegroundColor Red
    Write-Host $ProjectRoot
    exit 1
}


# ============================================================
# PBIP
# ============================================================

$PbipFiles = Get-ChildItem `
    -Path $ProjectRoot `
    -Filter "*.pbip" `
    -File


Write-Host "============================================================"
Write-Host "PBIP PROJECT"
Write-Host "============================================================"

if ($PbipFiles) {

    foreach ($File in $PbipFiles) {

        Write-Host "PASS | $($File.Name)"
    }
}
else {

    Write-Host "FAIL | No .pbip file found" -ForegroundColor Red
}


# ============================================================
# REPORT / SEMANTIC MODEL FOLDERS
# ============================================================

$ReportFolder = Get-ChildItem `
    -Path $ProjectRoot `
    -Directory |
    Where-Object Name -Like "*.Report" |
    Select-Object -First 1


$ModelFolder = Get-ChildItem `
    -Path $ProjectRoot `
    -Directory |
    Where-Object Name -Like "*.SemanticModel" |
    Select-Object -First 1


Write-Host ""
Write-Host "============================================================"
Write-Host "PROJECT FOLDERS"
Write-Host "============================================================"


if ($ReportFolder) {

    Write-Host "PASS | Report        | $($ReportFolder.FullName)"
}
else {

    Write-Host "FAIL | Report folder not found" -ForegroundColor Red
}


if ($ModelFolder) {

    Write-Host "PASS | SemanticModel | $($ModelFolder.FullName)"
}
else {

    Write-Host "FAIL | SemanticModel folder not found" -ForegroundColor Red
}


# ============================================================
# REPORT FILE INVENTORY
# ============================================================

if ($ReportFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "REPORT FILE INVENTORY"
    Write-Host "============================================================"

    Get-ChildItem `
        -Path $ReportFolder.FullName `
        -Recurse `
        -File |
        Sort-Object FullName |
        ForEach-Object {

            $Relative = $_.FullName.Substring(
                $ReportFolder.FullName.Length
            ).TrimStart("\")

            Write-Host $Relative
        }
}


# ============================================================
# REPORT PAGES
# ============================================================

if ($ReportFolder) {

    $PagesFolder = Join-Path `
        $ReportFolder.FullName `
        "definition\pages"


    Write-Host ""
    Write-Host "============================================================"
    Write-Host "REPORT PAGES"
    Write-Host "============================================================"


    if (Test-Path $PagesFolder) {

        $PageFolders = Get-ChildItem `
            -Path $PagesFolder `
            -Directory


        Write-Host "Page count: $($PageFolders.Count)"
        Write-Host ""


        foreach ($Page in $PageFolders) {

            $PageJson = Join-Path `
                $Page.FullName `
                "page.json"


            if (Test-Path $PageJson) {

                try {

                    $Json = Get-Content `
                        $PageJson `
                        -Raw |
                        ConvertFrom-Json


                    $DisplayName = $Json.displayName

                    if (-not $DisplayName) {

                        $DisplayName = "(no display name)"
                    }


                    Write-Host "PAGE"
                    Write-Host "  Folder : $($Page.Name)"
                    Write-Host "  Name   : $DisplayName"


                    $VisualFolder = Join-Path `
                        $Page.FullName `
                        "visuals"


                    if (Test-Path $VisualFolder) {

                        $Visuals = Get-ChildItem `
                            -Path $VisualFolder `
                            -Directory


                        Write-Host "  Visuals: $($Visuals.Count)"
                    }
                    else {

                        Write-Host "  Visuals: 0"
                    }


                    Write-Host ""
                }
                catch {

                    Write-Host "PAGE"
                    Write-Host "  Folder : $($Page.Name)"
                    Write-Host "  ERROR  : Could not parse page.json"
                    Write-Host ""
                }

            }

        }

    }
    else {

        Write-Host "PBIR pages folder not found."
        Write-Host ""
        Write-Host "The project may use a different report format."
    }
}


# ============================================================
# VISUAL TYPES
# ============================================================

if ($ReportFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "VISUAL TYPES"
    Write-Host "============================================================"


    $VisualFiles = Get-ChildItem `
        -Path $ReportFolder.FullName `
        -Filter "visual.json" `
        -Recurse `
        -File


    $VisualTypes = @()


    foreach ($File in $VisualFiles) {

        try {

            $Json = Get-Content `
                $File.FullName `
                -Raw |
                ConvertFrom-Json


            $Type = $Json.visual.visualType


            if (-not $Type) {

                $Type = $Json.visualType
            }


            if (-not $Type) {

                $Type = "(unknown)"
            }


            $VisualTypes += $Type
        }
        catch {

            $VisualTypes += "(parse error)"
        }

    }


    if ($VisualTypes.Count -gt 0) {

        $VisualTypes |
            Group-Object |
            Sort-Object Count -Descending |
            ForEach-Object {

                Write-Host (
                    "{0,4} | {1}" -f
                    $_.Count,
                    $_.Name
                )
            }

    }
    else {

        Write-Host "No visual.json files found."
    }
}


# ============================================================
# SEMANTIC MODEL FILES
# ============================================================

if ($ModelFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "SEMANTIC MODEL FILES"
    Write-Host "============================================================"


    $TmdlFiles = Get-ChildItem `
        -Path $ModelFolder.FullName `
        -Filter "*.tmdl" `
        -Recurse `
        -File


    Write-Host "TMDL files: $($TmdlFiles.Count)"
    Write-Host ""


    foreach ($File in $TmdlFiles) {

        $Relative = $File.FullName.Substring(
            $ModelFolder.FullName.Length
        ).TrimStart("\")

        Write-Host $Relative
    }
}


# ============================================================
# TABLE DEFINITIONS
# ============================================================

if ($ModelFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "MODEL TABLE DEFINITIONS"
    Write-Host "============================================================"


    $TableFolder = Join-Path `
        $ModelFolder.FullName `
        "definition\tables"


    if (Test-Path $TableFolder) {

        Get-ChildItem `
            -Path $TableFolder `
            -Filter "*.tmdl" `
            -File |
            Sort-Object Name |
            ForEach-Object {

                Write-Host $_.BaseName
            }

    }
    else {

        Write-Host "Table definition folder not found."
    }
}


# ============================================================
# RELATIONSHIPS
# ============================================================

if ($ModelFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "RELATIONSHIP FILE"
    Write-Host "============================================================"


    $RelationshipFiles = Get-ChildItem `
        -Path $ModelFolder.FullName `
        -Filter "*relationship*.tmdl" `
        -Recurse `
        -File


    if ($RelationshipFiles) {

        foreach ($File in $RelationshipFiles) {

            Write-Host ""
            Write-Host "FILE: $($File.FullName)"
            Write-Host ""

            Get-Content $File.FullName
        }

    }
    else {

        Write-Host "No relationship TMDL file found."
    }
}


# ============================================================
# MEASURE INVENTORY
# ============================================================

if ($ModelFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "MEASURES"
    Write-Host "============================================================"


    $MeasureLines = Get-ChildItem `
        -Path $ModelFolder.FullName `
        -Filter "*.tmdl" `
        -Recurse `
        -File |
        Select-String `
            -Pattern "^\s*measure\s+"


    if ($MeasureLines) {

        Write-Host "Measure count: $($MeasureLines.Count)"
        Write-Host ""

        foreach ($Match in $MeasureLines) {

            Write-Host $Match.Line.Trim()
        }

    }
    else {

        Write-Host "Measure count: 0"
    }
}


# ============================================================
# DATE TABLE CHECK
# ============================================================

if ($ModelFolder) {

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "DATE MODEL INDICATORS"
    Write-Host "============================================================"


    $DateMatches = Get-ChildItem `
        -Path $ModelFolder.FullName `
        -Filter "*.tmdl" `
        -Recurse `
        -File |
        Select-String `
            -Pattern "dim_date|Dato|reporting_date|dateTable"


    if ($DateMatches) {

        foreach ($Match in $DateMatches) {

            Write-Host (
                "{0}: {1}" -f
                $Match.Path,
                $Match.Line.Trim()
            )
        }

    }
    else {

        Write-Host "No date-model indicators found."
    }
}


# ============================================================
# FINAL
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "STATUS COMPLETE"
Write-Host "============================================================"
Write-Host ""

Write-Host "Copy the output from this script into Copilot."
Write-Host ""