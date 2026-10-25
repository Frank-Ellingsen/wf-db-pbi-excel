# Script to populate all 28 template visual containers in 99_Template with useful, professional visuals
param(
    [string]$VisualsDir = "c:\Users\frank\Desktop\WF1\powerbi\pbi-rep-project.Report\definition\pages\510fa5825560425f2411\visuals"
)

$ErrorActionPreference = "Stop"

function ColProj($entity, $prop, $active = $true) {
    return [ordered]@{
        field = [ordered]@{
            Column = [ordered]@{
                Expression = [ordered]@{
                    SourceRef = [ordered]@{
                        Entity = $entity
                    }
                }
                Property = $prop
            }
        }
        queryRef = "$entity.$prop"
        nativeQueryRef = $prop
        active = $active
    }
}

function MeasProj($prop) {
    return [ordered]@{
        field = [ordered]@{
            Measure = [ordered]@{
                Expression = [ordered]@{
                    SourceRef = [ordered]@{
                        Entity = "_Measures"
                    }
                }
                Property = $prop
            }
        }
        queryRef = "_Measures.$prop"
        nativeQueryRef = $prop
    }
}

function TitleObj($title) {
    return [ordered]@{
        title = @(
            [ordered]@{
                properties = [ordered]@{
                    text = [ordered]@{
                        expr = [ordered]@{
                            Literal = [ordered]@{
                                Value = "'$title'"
                            }
                        }
                    }
                }
            }
        )
    }
}

function MeasSort($prop, $dir = "Ascending") {
    return [ordered]@{
        sort = @(
            [ordered]@{
                field = [ordered]@{
                    Measure = [ordered]@{
                        Expression = [ordered]@{
                            SourceRef = [ordered]@{
                                Entity = "_Measures"
                            }
                        }
                        Property = $prop
                    }
                }
                direction = $dir
            }
        )
        isDefaultSort = $true
    }
}

function ColSort($entity, $prop, $dir = "Ascending") {
    return [ordered]@{
        sort = @(
            [ordered]@{
                field = [ordered]@{
                    Column = [ordered]@{
                        Expression = [ordered]@{
                            SourceRef = [ordered]@{
                                Entity = $entity
                            }
                        }
                        Property = $prop
                    }
                }
                direction = $dir
            }
        )
        isDefaultSort = $true
    }
}

# Update Visual Helper
function Update-VisualContainer($id, $visualType, $title, $queryState, $sortDef = $null, $extraVisualProps = @{}) {
    $file = Join-Path $VisualsDir "$id\visual.json"
    if (-not (Test-Path $file)) {
        Write-Warning "File not found: $file"
        return
    }

    $raw = Get-Content $file -Raw | ConvertFrom-Json
    
    $query = [ordered]@{
        queryState = $queryState
    }
    if ($sortDef) {
        $query["sortDefinition"] = $sortDef
    }

    $visualObj = [ordered]@{
        visualType = $visualType
        query = $query
        visualContainerObjects = (TitleObj $title)
        drillFilterOtherVisuals = $true
    }

    foreach ($k in $extraVisualProps.Keys) {
        $visualObj[$k] = $extraVisualProps[$k]
    }

    $outJson = [ordered]@{
        "`$schema" = $raw.'$schema'
        name = $raw.name
        position = $raw.position
        visual = $visualObj
    }

    if ($null -ne $raw.isHidden) {
        $outJson["isHidden"] = $raw.isHidden
    }

    $jsonStr = $outJson | ConvertTo-Json -Depth 20
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($file, $jsonStr, $utf8NoBom)
    Write-Host "Updated [$id] -> $visualType : $title"
}

Write-Host "============================================================"
Write-Host "POPULATING VISUALS IN 99_TEMPLATE"
Write-Host "============================================================"

# ROW 0
# 1. 332c2860a27ebde49468 - cardVisual (10, 0)
Update-VisualContainer "332c2860a27ebde49468" "cardVisual" "Avvik YTD (Budsjett - Regnskap)" `
    ([ordered]@{ Data = [ordered]@{ projections = @((MeasProj "ERP Avvik YTD")) } })

# 2. e052845b433a102224bd - clusteredBarChart (300, 0)
Update-VisualContainer "e052845b433a102224bd" "clusteredBarChart" "Avvik per Tjenesteomrade" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_kostra_function" "service_area_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Avvik")) }
    }) (MeasSort "ERP Avvik" "Ascending")

# 3. 573dc65b983a6da7ba8a - donutChart (590, 0)
Update-VisualContainer "573dc65b983a6da7ba8a" "donutChart" "Regnskap per Kontoklasse" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_account" "account_class_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    })

# 4. bebdf37f74b66cc80c52 - treemap (880, 0)
Update-VisualContainer "bebdf37f74b66cc80c52" "treemap" "Kostnadsfordeling Tjenesteomrader" `
    ([ordered]@{
        Group = [ordered]@{ projections = @((ColProj "dim_kostra_function" "service_area_name")) }
        Values = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    })

# 5. 4d748e076ad7a8e5feb4 - decompositionTreeVisual (1170, 0)
Update-VisualContainer "4d748e076ad7a8e5feb4" "decompositionTreeVisual" "Avviksdiagnose (Decomposition Tree)" `
    ([ordered]@{
        Analyze = [ordered]@{ projections = @((MeasProj "ERP Avvik")) }
        ExplainBy = [ordered]@{ projections = @(
            (ColProj "dim_account" "account_class_name"),
            (ColProj "dim_account" "main_group_name"),
            (ColProj "dim_kostra_function" "service_area_name"),
            (ColProj "dim_account" "account_name")
        ) }
    }) (MeasSort "ERP Avvik" "Ascending")

# 6. cad107203ca53e6c6df9 - lineStackedColumnComboChart (1460, 0)
Update-VisualContainer "cad107203ca53e6c6df9" "lineStackedColumnComboChart" "Manedlig Avvik & Avvik %" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Avvik")) }
        Y2 = [ordered]@{ projections = @((MeasProj "ERP Avvik %")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 7. 6bc2a74bf05c8f26d4e0 - tableEx (1750, 0)
Update-VisualContainer "6bc2a74bf05c8f26d4e0" "tableEx" "Konto Avviksoversikt" `
    ([ordered]@{
        Values = [ordered]@{ projections = @(
            (ColProj "dim_account" "account_name"),
            (MeasProj "ERP Budsjett"),
            (MeasProj "ERP Regnskap"),
            (MeasProj "ERP Avvik")
        ) }
    }) (MeasSort "ERP Avvik" "Ascending")


# ROW 1
# 8. 7891686011d0cd4651b1 - pivotTable (10, 290)
Update-VisualContainer "7891686011d0cd4651b1" "pivotTable" "Kontoplan Hierarki YTD" `
    ([ordered]@{
        Rows = [ordered]@{ projections = @(
            (ColProj "dim_account" "main_group_name"),
            (ColProj "dim_account" "account_name")
        ) }
        Values = [ordered]@{ projections = @(
            (MeasProj "ERP Budsjett YTD"),
            (MeasProj "ERP Regnskap YTD"),
            (MeasProj "ERP Avvik YTD"),
            (MeasProj "ERP Avvik YTD %")
        ) }
    }) (MeasSort "ERP Avvik YTD" "Ascending")

# 9. c1a93ebb328379eb2ca6 - columnChart (300, 290)
Update-VisualContainer "c1a93ebb328379eb2ca6" "columnChart" "Manedlig Regnskap" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 10. e82f421fe9a3fe72a455 - funnel (590, 290)
Update-VisualContainer "e82f421fe9a3fe72a455" "funnel" "Kostnadstrapp Tjenesteomrader" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_kostra_function" "service_area_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    })

# 11. 20714f6b96fc0ca37d6d - filledMap (880, 290)
Update-VisualContainer "20714f6b96fc0ca37d6d" "filledMap" "Regnskap per Lokasjon / Avdeling" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "fact_erp_finance" "location")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    })

# 12. 5ad2bbb0113d1510923b - waterfallChart (1170, 290)
Update-VisualContainer "5ad2bbb0113d1510923b" "waterfallChart" "Avviksbro per Hovedgruppe" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_account" "main_group_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Avvik")) }
    })

# 13. 47e27970217bb58ee0bf - lineClusteredColumnComboChart (1460, 290)
Update-VisualContainer "47e27970217bb58ee0bf" "lineClusteredColumnComboChart" "Regnskap vs Budsjett Manedlig" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
        Y2 = [ordered]@{ projections = @((MeasProj "ERP Budsjett")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 14. d9c9b881e9f4e43e11dd - cardVisual (1750, 290)
Update-VisualContainer "d9c9b881e9f4e43e11dd" "cardVisual" "Budsjett YTD" `
    ([ordered]@{ Data = [ordered]@{ projections = @((MeasProj "ERP Budsjett YTD")) } })


# ROW 2
# 15. e010d04b35a93ef23631 - pivotTable (10, 580)
Update-VisualContainer "e010d04b35a93ef23631" "pivotTable" "KOSTRA Funksjonsmatrise YTD" `
    ([ordered]@{
        Rows = [ordered]@{ projections = @(
            (ColProj "dim_kostra_function" "main_function_name"),
            (ColProj "dim_kostra_function" "service_area_name"),
            (ColProj "dim_kostra_function" "kostra_function_name")
        ) }
        Values = [ordered]@{ projections = @(
            (MeasProj "ERP Budsjett YTD"),
            (MeasProj "ERP Regnskap YTD"),
            (MeasProj "ERP Avvik YTD"),
            (MeasProj "ERP Avvik YTD %")
        ) }
    }) (MeasSort "ERP Avvik YTD" "Ascending")

# 16. fdce398a9a9f12d91017 - barChart (300, 580)
Update-VisualContainer "fdce398a9a9f12d91017" "barChart" "Avvik per Konto YTD" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_account" "account_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Avvik YTD")) }
    }) (MeasSort "ERP Avvik YTD" "Ascending")

# 17. 2565965d93f316e47d3c - areaChart (590, 580)
Update-VisualContainer "2565965d93f316e47d3c" "areaChart" "Akkumulert Regnskap (S-kurve)" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap Running")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 18. daa85b1183a7d31795f0 - clusteredBarChart (880, 580)
Update-VisualContainer "daa85b1183a7d31795f0" "clusteredBarChart" "Regnskap per Ansvar / Niva 1" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_budget_organization" "budget_level_1_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    }) (MeasSort "ERP Regnskap" "Descending")

# 19. a8691d904ab1e4c7d2ae - scatterChart (1170, 580)
Update-VisualContainer "a8691d904ab1e4c7d2ae" "scatterChart" "Diagnose: Regnskap vs Budsjett" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_account" "account_name")) }
        X = [ordered]@{ projections = @((MeasProj "ERP Budsjett")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
        Tooltips = [ordered]@{ projections = @((MeasProj "ERP Avvik"), (MeasProj "ERP Avvik %")) }
    })

# 20. 507ed135f35d3a3e4ded - kpi (1460, 580)
Update-VisualContainer "507ed135f35d3a3e4ded" "kpi" "Regnskap YTD vs Budsjettmal" `
    ([ordered]@{
        Indicator = [ordered]@{ projections = @((MeasProj "ERP Regnskap YTD")) }
        Goal = [ordered]@{ projections = @((MeasProj "ERP Budsjett YTD")) }
        TrendLine = [ordered]@{ projections = @((ColProj "dim_date" "date")) }
    }) (MeasSort "ERP Regnskap YTD" "Descending")

# 21. 59619af6b25da51b7a3b - cardVisual (1750, 580)
Update-VisualContainer "59619af6b25da51b7a3b" "cardVisual" "Avvik YTD %" `
    ([ordered]@{ Data = [ordered]@{ projections = @((MeasProj "ERP Avvik YTD %")) } })


# ROW 3
# 22. 4ef64aa1530c20c95e24 - lineChart (10, 870)
Update-VisualContainer "4ef64aa1530c20c95e24" "lineChart" "Regnskap & Budsjett Trend" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap"), (MeasProj "ERP Budsjett")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 23. 73a02bd4c2049f6f1e6a - donutChart (300, 870)
Update-VisualContainer "73a02bd4c2049f6f1e6a" "donutChart" "Fordeling Hovedfunksjon" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_kostra_function" "main_function_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    })

# 24. aab65ece7d3e17bf6171 - hundredPercentStackedAreaChart (590, 870)
Update-VisualContainer "aab65ece7d3e17bf6171" "hundredPercentStackedAreaChart" "Kontoklasse Andel over Tid" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Series = [ordered]@{ projections = @((ColProj "dim_account" "account_class_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 25. c74047c6fef809985413 - keyDriversVisual (880, 870)
Update-VisualContainer "c74047c6fef809985413" "keyDriversVisual" "Avviksdrivere (Key Influencers)" `
    ([ordered]@{
        Analyze = [ordered]@{ projections = @((MeasProj "ERP Avvik")) }
        ExplainBy = [ordered]@{ projections = @(
            (ColProj "dim_account" "main_group_name"),
            (ColProj "dim_kostra_function" "service_area_name")
        ) }
    })

# 26. 5e8fef9740d5e9d934a0 - ribbonChart (1170, 870)
Update-VisualContainer "5e8fef9740d5e9d934a0" "ribbonChart" "Tjenesteomrader Rangering (Ribbon)" `
    ([ordered]@{
        Category = [ordered]@{ projections = @((ColProj "dim_date" "year_month")) }
        Series = [ordered]@{ projections = @((ColProj "dim_kostra_function" "service_area_name")) }
        Y = [ordered]@{ projections = @((MeasProj "ERP Regnskap")) }
    }) (ColSort "dim_date" "year_month" "Ascending")

# 27. 6f462b0da17a310de414 - slicer (1460, 870)
Update-VisualContainer "6f462b0da17a310de414" "slicer" "Filter: Tjenesteomrade" `
    ([ordered]@{
        Values = [ordered]@{ projections = @((ColProj "dim_kostra_function" "service_area_name")) }
    })

# 28. de64282cb5fd4ccc23f7 - cardVisual (1750, 870)
Update-VisualContainer "de64282cb5fd4ccc23f7" "cardVisual" "Datakvalitet Status" `
    ([ordered]@{ Data = [ordered]@{ projections = @((MeasProj "Overall Data Quality Status")) } })

Write-Host "============================================================"
Write-Host "ALL 28 TEMPLATE VISUALS POPULATED SUCCESSFULLY!"
Write-Host "============================================================"
