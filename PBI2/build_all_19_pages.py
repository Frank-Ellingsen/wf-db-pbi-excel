import os, sys, json, uuid, shutil

sys.stdout.reconfigure(encoding='utf-8')

true = True
false = False
null = None

report_pages_dir = r'c:\Users\frank\Desktop\WF1\PBI2\pbi-rep-project2.Report\definition\pages'
pages_json_path = os.path.join(report_pages_dir, 'pages.json')

def make_id():
    return uuid.uuid4().hex[:20]

def save_page(page_dict, visuals_list):
    page_name = page_dict['name']
    page_folder = os.path.join(report_pages_dir, page_name)
    os.makedirs(page_folder, exist_ok=True)
    
    with open(os.path.join(page_folder, 'page.json'), 'w', encoding='utf-8') as f:
        json.dump(page_dict, f, indent=2, ensure_ascii=False)
        
    vis_dir = os.path.join(page_folder, 'visuals')
    os.makedirs(vis_dir, exist_ok=True)
    
    for v_id, v_content in visuals_list:
        v_folder = os.path.join(vis_dir, v_id)
        os.makedirs(v_folder, exist_ok=True)
        with open(os.path.join(v_folder, 'visual.json'), 'w', encoding='utf-8') as f:
            json.dump(v_content, f, indent=2, ensure_ascii=False)

def create_slicer(entity, prop, display_name, x, y, w, h, sync_name, z=1000):
    vid = make_id()
    return vid, {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": vid,
        "position": { "x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z },
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": { "SourceRef": { "Entity": entity } },
                                        "Property": prop
                                    }
                                },
                                "queryRef": f"{entity}.{prop}",
                                "nativeQueryRef": prop,
                                "active": true
                            }
                        ]
                    }
                }
            },
            "objects": {
                "data": [
                    { "properties": { "mode": { "expr": { "Literal": { "Value": "'Dropdown'" } } } } }
                ]
            },
            "visualContainerObjects": {
                "title": [
                    { "properties": { "text": { "expr": { "Literal": { "Value": f"'{display_name}'" } } } } }
                ]
            },
            "syncGroup": {
                "groupName": sync_name,
                "fieldChanges": true,
                "filterChanges": true
            },
            "drillFilterOtherVisuals": true
        }
    }

def create_kpi_card(measure, display_title, color_measure, x, y, w, h, z=2000):
    vid = make_id()
    v_obj = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": vid,
        "position": { "x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z },
        "visual": {
            "visualType": "cardVisual",
            "query": {
                "queryState": {
                    "Data": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": { "SourceRef": { "Entity": "_Measures" } },
                                        "Property": measure
                                    }
                                },
                                "queryRef": f"_Measures.{measure}",
                                "nativeQueryRef": measure
                            }
                        ]
                    }
                }
            },
            "visualContainerObjects": {
                "title": [
                    { "properties": { "text": { "expr": { "Literal": { "Value": f"'{display_title}'" } } } } }
                ]
            },
            "drillFilterOtherVisuals": true
        }
    }
    if color_measure:
        v_obj["visual"]["objects"] = {
            "value": [
                {
                    "properties": {
                        "fontColor": {
                            "solid": {
                                "color": {
                                    "expr": {
                                        "Measure": {
                                            "Expression": { "SourceRef": { "Entity": "_Measures" } },
                                            "Property": color_measure
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "selector": {
                        "data": [ { "dataViewWildcard": { "matchingOption": 0 } } ],
                        "metadata": f"_Measures.{measure}"
                    }
                }
            ]
        }
    return vid, v_obj

def create_header_banner(title_text, subtitle_text, x=40, y=15, w=1180, h=80, z=500):
    vid = make_id()
    return vid, {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": vid,
        "position": { "x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z },
        "visual": {
            "visualType": "cardVisual",
            "query": {
                "queryState": {
                    "Data": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": { "SourceRef": { "Entity": "_Measures" } },
                                        "Property": "Story Forecast Narrative"
                                    }
                                },
                                "queryRef": "_Measures.Story Forecast Narrative",
                                "nativeQueryRef": "Story Forecast Narrative"
                            }
                        ]
                    }
                }
            },
            "visualContainerObjects": {
                "title": [
                    {
                        "properties": {
                            "text": { "expr": { "Literal": { "Value": f"'{title_text} | {subtitle_text}'" } } }
                        }
                    }
                ]
            },
            "drillFilterOtherVisuals": true
        }
    }

def get_standard_slicers():
    return [
        create_slicer("dim_date", "year", "År", 1250, 15, 140, 75, "sync_year", 1010),
        create_slicer("dim_date", "tertial", "Tertial", 1400, 15, 140, 75, "sync_tertial", 1020),
        create_slicer("dim_account", "main_group_name", "Kontogruppe", 1550, 15, 170, 75, "sync_group", 1030),
        create_slicer("dim_budget_organization", "budget_level_2_name", "Organisasjon", 1730, 15, 150, 75, "sync_org", 1040)
    ]

def create_variance_matrix_with_databars(title, x=1220, y=210, w=660, h=840, z=3000):
    vid = make_id()
    return vid, {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": vid,
        "position": { "x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z },
        "visual": {
            "visualType": "pivotTable",
            "query": {
                "queryState": {
                    "Rows": {
                        "projections": [
                            {
                                "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } },
                                "queryRef": "dim_account.main_group_name",
                                "nativeQueryRef": "main_group_name",
                                "active": true
                            },
                            {
                                "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                                "queryRef": "dim_account.account_name",
                                "nativeQueryRef": "account_name",
                                "active": true
                            }
                        ]
                    },
                    "Values": {
                        "projections": [
                            {
                                "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett YTD" } },
                                "queryRef": "_Measures.ERP Budsjett YTD",
                                "nativeQueryRef": "ERP Budsjett YTD"
                            },
                            {
                                "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap YTD" } },
                                "queryRef": "_Measures.ERP Regnskap YTD",
                                "nativeQueryRef": "ERP Regnskap YTD"
                            },
                            {
                                "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik YTD" } },
                                "queryRef": "_Measures.ERP Avvik YTD",
                                "nativeQueryRef": "ERP Avvik YTD"
                            },
                            {
                                "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik YTD %" } },
                                "queryRef": "_Measures.ERP Avvik YTD %",
                                "nativeQueryRef": "ERP Avvik YTD %"
                            }
                        ]
                    }
                }
            },
            "objects": {
                "grid": [
                    { "properties": { "gridVertical": { "expr": { "Literal": { "Value": "false" } } } } }
                ],
                "columnFormatting": [
                    {
                        "properties": {
                            "dataBars": {
                                "positiveColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#16A34A'" } } } } },
                                "negativeColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#DC2626'" } } } } },
                                "axisColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#64748B'" } } } } },
                                "reverseDirection": { "expr": { "Literal": { "Value": "false" } } },
                                "hideText": { "expr": { "Literal": { "Value": "false" } } },
                                "totalMatchingOption": { "expr": { "Literal": { "Value": "1L" } } }
                            }
                        },
                        "selector": { "metadata": "_Measures.ERP Avvik YTD" }
                    }
                ]
            },
            "visualContainerObjects": {
                "title": [
                    { "properties": { "text": { "expr": { "Literal": { "Value": f"'{title}'" } } } } }
                ]
            },
            "drillFilterOtherVisuals": true
        }
    }

def create_clustered_bar(cat_entity, cat_prop, value_measure, title, x=40, y=210, w=1160, h=840, color_measure="ERP RAG Color", z=2500):
    vid = make_id()
    return vid, {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": vid,
        "position": { "x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z },
        "visual": {
            "visualType": "clusteredBarChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": { "SourceRef": { "Entity": cat_entity } },
                                        "Property": cat_prop
                                    }
                                },
                                "queryRef": f"{cat_entity}.{cat_prop}",
                                "nativeQueryRef": cat_prop,
                                "active": true
                            }
                        ]
                    },
                    "Y": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": { "SourceRef": { "Entity": "_Measures" } },
                                        "Property": value_measure
                                    }
                                },
                                "queryRef": f"_Measures.{value_measure}",
                                "nativeQueryRef": value_measure
                            }
                        ]
                    }
                },
                "sortDefinition": {
                    "sort": [
                        {
                            "field": {
                                "Measure": {
                                    "Expression": { "SourceRef": { "Entity": "_Measures" } },
                                    "Property": value_measure
                                }
                            },
                            "direction": "Descending"
                        }
                    ],
                    "isDefaultSort": true
                }
            },
            "objects": {
                "dataPoint": [
                    {
                        "properties": {
                            "fill": {
                                "solid": {
                                    "color": {
                                        "expr": {
                                            "Measure": {
                                                "Expression": { "SourceRef": { "Entity": "_Measures" } },
                                                "Property": color_measure
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "visualContainerObjects": {
                "title": [
                    { "properties": { "text": { "expr": { "Literal": { "Value": f"'{title}'" } } } } }
                ]
            },
            "drillFilterOtherVisuals": true
        }
    }

all_pages = []

# ==========================================
# PAGE 1: 01_SCurve_EAC
# ==========================================
p1_id = "p01_scurve_eac_0001"
p1_visuals = []
p1_visuals.append(create_header_banner("01 Akkumulert S-Kurve & Helårsprognose (EAC)", "Test: Gir S-kurven tilstrekkelig tidlig varsel om at 17,2M årsrammen overskrides?"))
p1_visuals.extend(get_standard_slicers())
p1_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD (P08)", None, 40, 105, 275, 95, 2010))
p1_visuals.append(create_kpi_card("ERP Budsjett YTD", "Budsjett YTD (P08)", None, 335, 105, 275, 95, 2020))
p1_visuals.append(create_kpi_card("ERP Avvik YTD", "Avvik YTD", "ERP RAG Color", 630, 105, 275, 95, 2030))
p1_visuals.append(create_kpi_card("ERP Forecast EOY", "Helårsprognose EAC", "ERP Forecast EOY Color", 925, 105, 275, 95, 2040))

# Line chart S-Curve
p1_scurve_id = make_id()
p1_visuals.append((p1_scurve_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p1_scurve_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "lineChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "date" } },
                            "queryRef": "dim_date.date",
                            "nativeQueryRef": "date",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett Running" } },
                            "queryRef": "_Measures.ERP Budsjett Running",
                            "nativeQueryRef": "ERP Budsjett Running"
                        },
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap Running" } },
                            "queryRef": "_Measures.ERP Regnskap Running",
                            "nativeQueryRef": "ERP Regnskap Running"
                        },
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Actual + Forecast" } },
                            "queryRef": "_Measures.ERP Actual + Forecast",
                            "nativeQueryRef": "ERP Actual + Forecast"
                        }
                    ]
                }
            },
            "sortDefinition": {
                "sort": [ { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "date" } }, "direction": "Ascending" } ],
                "isDefaultSort": true
            }
        },
        "objects": {
            "forecast": [
                {
                    "properties": {
                        "show": { "expr": { "Literal": { "Value": "true" } } },
                        "displayName": { "expr": { "Literal": { "Value": "'AI Forecast'" } } },
                        "transform": {
                            "algorithm": "Forecast",
                            "parameters": [
                                { "Literal": { "Value": "7D" }, "Name": "Unit" },
                                { "Literal": { "Value": "4D" }, "Name": "ForecastLength" },
                                { "Literal": { "Value": "0D" }, "Name": "IgnoreLast" },
                                { "Literal": { "Value": "0.9D" }, "Name": "ConfidenceLevel" }
                            ]
                        }
                    },
                    "selector": { "metadata": "_Measures.ERP Regnskap Running", "id": "1" }
                }
            ]
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Akkumulert S-Kurve & Helårsprognose (EAC)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p1_visuals.append(create_variance_matrix_with_databars("Månedlig Avstemming & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p1_id,
    "displayName": "01_SCurve_EAC",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p1_visuals)
all_pages.append(p1_id)

# ==========================================
# PAGE 2: 02_Waterfall_Bridge
# ==========================================
p2_id = "p02_waterfall_0000002"
p2_visuals = []
p2_visuals.append(create_header_banner("02 Avviksbro (-1,29 MNOK) Budsjett til Faktisk", "Test: Kan ledelsen umiddelbart identifisere hvilke poster som spiser avviket?"))
p2_visuals.extend(get_standard_slicers())
p2_visuals.append(create_kpi_card("ERP Budsjett YTD", "Budsjett YTD", None, 40, 105, 275, 95, 2010))
p2_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 335, 105, 275, 95, 2020))
p2_visuals.append(create_kpi_card("ERP Avvik YTD", "Netto Avvik", "ERP RAG Color", 630, 105, 275, 95, 2030))
p2_visuals.append(create_kpi_card("ERP Avvik YTD %", "Avvik %", "ERP RAG Color", 925, 105, 275, 95, 2040))

p2_wf_id = make_id()
p2_visuals.append((p2_wf_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p2_wf_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "waterfallChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } },
                            "queryRef": "dim_account.main_group_name",
                            "nativeQueryRef": "main_group_name",
                            "active": true
                        },
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                            "queryRef": "dim_account.account_name",
                            "nativeQueryRef": "account_name",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } },
                            "queryRef": "_Measures.ERP Avvik",
                            "nativeQueryRef": "ERP Avvik"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Avviksbro per Hovedgruppe og Konto (Drilldown)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p2_visuals.append(create_variance_matrix_with_databars("Avvikstabell med Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p2_id,
    "displayName": "02_Waterfall_Bridge",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p2_visuals)
all_pages.append(p2_id)

# ==========================================
# PAGE 3: 03_Monthly_Budget_Actual
# ==========================================
p3_id = "p03_monthly_combo_003"
p3_visuals = []
p3_visuals.append(create_header_banner("03 Månedlig Regnskap vs Budsjett P01-P12", "Test: Hvordan fordeler forbruket seg over året, og når inntreffer avvikene?"))
p3_visuals.extend(get_standard_slicers())
p3_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 40, 105, 360, 95, 2010))
p3_visuals.append(create_kpi_card("ERP Budsjett YTD", "Budsjett YTD", None, 420, 105, 360, 95, 2020))
p3_visuals.append(create_kpi_card("ERP Budsjettforbruk %", "Budsjettforbruk %", "ERP RAG Color", 800, 105, 400, 95, 2030))

p3_combo_id = make_id()
p3_visuals.append((p3_combo_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p3_combo_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "lineClusteredColumnComboChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "year" } },
                            "queryRef": "dim_date.year",
                            "nativeQueryRef": "year",
                            "active": true
                        },
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "tertial" } },
                            "queryRef": "dim_date.tertial",
                            "nativeQueryRef": "tertial",
                            "active": true
                        },
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "month_name" } },
                            "queryRef": "dim_date.month_name",
                            "nativeQueryRef": "month_name",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } },
                            "queryRef": "_Measures.ERP Regnskap",
                            "nativeQueryRef": "ERP Regnskap"
                        },
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett" } },
                            "queryRef": "_Measures.ERP Budsjett",
                            "nativeQueryRef": "ERP Budsjett"
                        }
                    ]
                },
                "Y2": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjettforbruk %" } },
                            "queryRef": "_Measures.ERP Budsjettforbruk %",
                            "nativeQueryRef": "ERP Budsjettforbruk %"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Månedlig Regnskap vs Budsjett med Forbrukstakt (Drilldown)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p3_visuals.append(create_variance_matrix_with_databars("Månedlig Fordeling & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p3_id,
    "displayName": "03_Monthly_Budget_Actual",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p3_visuals)
all_pages.append(p3_id)

# ==========================================
# PAGE 4: 04_Diverging_Variance
# ==========================================
p4_id = "p04_diverging_mom_004"
p4_visuals = []
p4_visuals.append(create_header_banner("04 Diverging MoM Månedsvis Avviksanalyse", "Test: Viser avvikene fra null-baseline retningsendringer raskere enn kakediagram?"))
p4_visuals.extend(get_standard_slicers())
p4_visuals.append(create_kpi_card("ERP Avvik YTD", "Avvik YTD", "ERP RAG Color", 40, 105, 360, 95, 2010))
p4_visuals.append(create_kpi_card("ERP Absolutt Avvik", "Absolutt Avvik", None, 420, 105, 360, 95, 2020))
p4_visuals.append(create_kpi_card("ERP Månedlig Gjennomsnitt", "Snittforbruk/mnd", None, 800, 105, 400, 95, 2030))

p4_visuals.append(create_clustered_bar("dim_date", "month_name", "ERP Avvik", "Diverging Månedsvis Avvik (RAG Fargekoding)"))
p4_visuals.append(create_variance_matrix_with_databars("Månedsvise Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p4_id,
    "displayName": "04_Diverging_Variance",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p4_visuals)
all_pages.append(p4_id)

# ==========================================
# PAGE 5: 05_Top_Account_Ranking
# ==========================================
p5_id = "p05_top_account_000005"
p5_visuals = []
p5_visuals.append(create_header_banner("05 Topp Kontoavvik Ranking", "Test: Hvilke 10 spesifikke konti må prioriteres i ledelsens tiltaksliste?"))
p5_visuals.extend(get_standard_slicers())
p5_visuals.append(create_kpi_card("ERP Største Kostnadsdriver Beløp", "Største Sprekk", "ERP RAG Color", 40, 105, 360, 95, 2010))
p5_visuals.append(create_kpi_card("ERP Total Negativ Kostnadsdriver", "Totale Sprekker", "ERP RAG Color", 420, 105, 360, 95, 2020))
p5_visuals.append(create_kpi_card("ERP Avvik YTD", "Netto Avvik", "ERP RAG Color", 800, 105, 400, 95, 2030))

p5_visuals.append(create_clustered_bar("dim_account", "account_name", "ERP Avvik", "Topp Kontoavvik Sortert Synkende (RAG Fargekoding)"))
p5_visuals.append(create_variance_matrix_with_databars("Kontorangering & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p5_id,
    "displayName": "05_Top_Account_Ranking",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p5_visuals)
all_pages.append(p5_id)

# ==========================================
# PAGE 6: 06_Part_To_Whole_Treemap
# ==========================================
p6_id = "p06_treemap_part2whole"
p6_visuals = []
p6_visuals.append(create_header_banner("06 Kostnadsstruktur & Proporsjoner (Treemap)", "Test: Gir treemap bedre oversikt over lønn vs drift enn tradisjonelle kakediagram?"))
p6_visuals.extend(get_standard_slicers())
p6_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 40, 105, 360, 95, 2010))
p6_visuals.append(create_kpi_card("ERP Lønnsandel %", "Lønnsandel %", None, 420, 105, 360, 95, 2020))
p6_visuals.append(create_kpi_card("ERP Driftsandel %", "Driftsandel %", None, 800, 105, 400, 95, 2030))

p6_tm_id = make_id()
p6_visuals.append((p6_tm_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p6_tm_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "treemap",
        "query": {
            "queryState": {
                "Group": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } },
                            "queryRef": "dim_account.main_group_name",
                            "nativeQueryRef": "main_group_name",
                            "active": true
                        },
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                            "queryRef": "dim_account.account_name",
                            "nativeQueryRef": "account_name",
                            "active": true
                        }
                    ]
                },
                "Values": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } },
                            "queryRef": "_Measures.ERP Regnskap",
                            "nativeQueryRef": "ERP Regnskap"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Kostnadsfordeling Hovedgrupper og Konti (Drilldown)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p6_visuals.append(create_variance_matrix_with_databars("Strukturmatrise & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p6_id,
    "displayName": "06_Part_To_Whole_Treemap",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p6_visuals)
all_pages.append(p6_id)

# ==========================================
# PAGE 7: 07_Turnus_Staffing_Spine
# ==========================================
p7_id = "p07_turnus_spine_0007"
p7_visuals = []
p7_visuals.append(create_header_banner("07 Bemanningsstruktur & Turnus (Spine / Tornado)", "Test: Viser diagrammet tydelig substitusjonen av fastlønn med overtid og vikarer?"))
p7_visuals.extend(get_standard_slicers())
p7_visuals.append(create_kpi_card("ERP Fastlønn Regnskap", "Fastlønn Ordinære", None, 40, 105, 360, 95, 2010))
p7_visuals.append(create_kpi_card("ERP Vikar Regnskap", "Vikarer / Eksterne", "ERP RAG Color", 420, 105, 360, 95, 2020))
p7_visuals.append(create_kpi_card("ERP Overtid Regnskap", "Overtidsutgifter", "ERP RAG Color", 800, 105, 400, 95, 2030))

p7_bar_id = make_id()
p7_visuals.append((p7_bar_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p7_bar_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "month_name" } },
                            "queryRef": "dim_date.month_name",
                            "nativeQueryRef": "month_name",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Fastlønn Regnskap" } },
                            "queryRef": "_Measures.ERP Fastlønn Regnskap",
                            "nativeQueryRef": "ERP Fastlønn Regnskap"
                        },
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Vikar Regnskap" } },
                            "queryRef": "_Measures.ERP Vikar Regnskap",
                            "nativeQueryRef": "ERP Vikar Regnskap"
                        },
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Overtid Regnskap" } },
                            "queryRef": "_Measures.ERP Overtid Regnskap",
                            "nativeQueryRef": "ERP Overtid Regnskap"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Bemanningsfordeling: Fastlønn vs Vikarer vs Overtid'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p7_visuals.append(create_variance_matrix_with_databars("Lønnsarter & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p7_id,
    "displayName": "07_Turnus_Staffing_Spine",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p7_visuals)
all_pages.append(p7_id)

# ==========================================
# PAGE 8: 08_Tertial_Slope
# ==========================================
p8_id = "p08_tertial_slope_008"
p8_visuals = []
p8_visuals.append(create_header_banner("08 Tertialdynamikk & Sesongvariasjon (Slope / Ribbon)", "Test: Akselererer kostnadene i T2 sammenlignet med T1?"))
p8_visuals.extend(get_standard_slicers())
p8_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 40, 105, 360, 95, 2010))
p8_visuals.append(create_kpi_card("ERP Tertial 1 Regnskap", "Regnskap T1", None, 420, 105, 360, 95, 2020))
p8_visuals.append(create_kpi_card("ERP Tertial 2 Regnskap", "Regnskap T2", "ERP RAG Color", 800, 105, 400, 95, 2030))

p8_ribbon_id = make_id()
p8_visuals.append((p8_ribbon_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p8_ribbon_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "ribbonChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "tertial" } },
                            "queryRef": "dim_date.tertial",
                            "nativeQueryRef": "tertial",
                            "active": true
                        }
                    ]
                },
                "Series": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } },
                            "queryRef": "dim_account.main_group_name",
                            "nativeQueryRef": "main_group_name",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } },
                            "queryRef": "_Measures.ERP Regnskap",
                            "nativeQueryRef": "ERP Regnskap"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Tertialutvikling per Hovedgruppe (Slope/Ribbon)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p8_visuals.append(create_variance_matrix_with_databars("Tertialoversikt & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p8_id,
    "displayName": "08_Tertial_Slope",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p8_visuals)
all_pages.append(p8_id)

# ==========================================
# PAGE 9: 09_Bullet_KPIs
# ==========================================
p9_id = "p09_bullet_kpis_00009"
p9_visuals = []
p9_visuals.append(create_header_banner("09 Bullet Graphs & KPI Måloppnåelse", "Test: Gir Tufte Bullet Graphs raskere risikovurdering enn standard dashboard-cards?"))
p9_visuals.extend(get_standard_slicers())

# 3 KPI visuals
p9_kpi1_id = make_id()
p9_visuals.append((p9_kpi1_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p9_kpi1_id,
    "position": { "x": 40, "y": 105, "z": 2000, "height": 340, "width": 360, "tabOrder": 2000 },
    "visual": {
        "visualType": "kpi",
        "query": {
            "queryState": {
                "Indicator": {
                    "projections": [ { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap YTD" } }, "queryRef": "_Measures.ERP Regnskap YTD", "nativeQueryRef": "ERP Regnskap YTD" } ]
                },
                "Goal": {
                    "projections": [ { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett YTD" } }, "queryRef": "_Measures.ERP Budsjett YTD", "nativeQueryRef": "ERP Budsjett YTD" } ]
                },
                "TrendLine": {
                    "projections": [ { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "date" } }, "queryRef": "dim_date.date", "nativeQueryRef": "date", "active": true } ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Regnskap YTD vs Budsjettmål'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))

p9_kpi2_id = make_id()
p9_visuals.append((p9_kpi2_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p9_kpi2_id,
    "position": { "x": 420, "y": 105, "z": 2000, "height": 340, "width": 360, "tabOrder": 2000 },
    "visual": {
        "visualType": "kpi",
        "query": {
            "queryState": {
                "Indicator": {
                    "projections": [ { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik YTD" } }, "queryRef": "_Measures.ERP Avvik YTD", "nativeQueryRef": "ERP Avvik YTD" } ]
                },
                "Goal": {
                    "projections": [ { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "Gauge EOY Target" } }, "queryRef": "_Measures.Gauge EOY Target", "nativeQueryRef": "Gauge EOY Target" } ]
                },
                "TrendLine": {
                    "projections": [ { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "date" } }, "queryRef": "dim_date.date", "nativeQueryRef": "date", "active": true } ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Avvik YTD mot Null-Toleranse'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))

p9_kpi3_id = make_id()
p9_visuals.append((p9_kpi3_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p9_kpi3_id,
    "position": { "x": 800, "y": 105, "z": 2000, "height": 340, "width": 400, "tabOrder": 2000 },
    "visual": {
        "visualType": "kpi",
        "query": {
            "queryState": {
                "Indicator": {
                    "projections": [ { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Forecast EOY" } }, "queryRef": "_Measures.ERP Forecast EOY", "nativeQueryRef": "ERP Forecast EOY" } ]
                },
                "Goal": {
                    "projections": [ { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Årsbudsjett" } }, "queryRef": "_Measures.ERP Årsbudsjett", "nativeQueryRef": "ERP Årsbudsjett" } ]
                },
                "TrendLine": {
                    "projections": [ { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "date" } }, "queryRef": "dim_date.date", "nativeQueryRef": "date", "active": true } ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Prognose EAC mot Årsbudsjett'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))

# Status table
p9_visuals.append(create_variance_matrix_with_databars("Konto Helsetilstand & Datastolper", 40, 470, 1840, 580))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p9_id,
    "displayName": "09_Bullet_KPIs",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p9_visuals)
all_pages.append(p9_id)

# ==========================================
# PAGE 10: 10_Account_Matrix_Heatmap
# ==========================================
p10_id = "p10_heatmap_matrix_01"
p10_visuals = []
p10_visuals.append(create_header_banner("10 Månedlig Kontomatrise & Heatmap", "Test: Avslører fargeintensiteten i cellene mønstre og unormale månedlige topper?"))
p10_visuals.extend(get_standard_slicers())
p10_visuals.append(create_kpi_card("ERP Avvik YTD", "Avvik YTD", "ERP RAG Color", 40, 105, 560, 95, 2010))
p10_visuals.append(create_kpi_card("ERP Absolutt Avvik", "Absolutt Avvik", None, 620, 105, 580, 95, 2020))

p10_mat_id = make_id()
p10_visuals.append((p10_mat_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p10_mat_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1840, "tabOrder": 2500 },
    "visual": {
        "visualType": "pivotTable",
        "query": {
            "queryState": {
                "Rows": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } },
                            "queryRef": "dim_account.main_group_name",
                            "nativeQueryRef": "main_group_name",
                            "active": true
                        },
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                            "queryRef": "dim_account.account_name",
                            "nativeQueryRef": "account_name",
                            "active": true
                        }
                    ]
                },
                "Columns": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "month_name" } },
                            "queryRef": "dim_date.month_name",
                            "nativeQueryRef": "month_name",
                            "active": true
                        }
                    ]
                },
                "Values": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } },
                            "queryRef": "_Measures.ERP Avvik",
                            "nativeQueryRef": "ERP Avvik"
                        }
                    ]
                }
            }
        },
        "objects": {
            "grid": [ { "properties": { "gridVertical": { "expr": { "Literal": { "Value": "false" } } } } } ],
            "columnFormatting": [
                {
                    "properties": {
                        "dataBars": {
                            "positiveColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#16A34A'" } } } } },
                            "negativeColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#DC2626'" } } } } },
                            "axisColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#64748B'" } } } } },
                            "reverseDirection": { "expr": { "Literal": { "Value": "false" } } },
                            "hideText": { "expr": { "Literal": { "Value": "false" } } },
                            "totalMatchingOption": { "expr": { "Literal": { "Value": "1L" } } }
                        }
                    },
                    "selector": { "metadata": "_Measures.ERP Avvik" }
                }
            ]
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Månedlig Kontomatrise P01-P12 med Betingede Datastolper'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p10_id,
    "displayName": "10_Account_Matrix_Heatmap",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p10_visuals)
all_pages.append(p10_id)

# ==========================================
# PAGE 11: 11_Scatter_Correlation
# ==========================================
p11_id = "p11_scatter_corr_0011"
p11_visuals = []
p11_visuals.append(create_header_banner("11 Korrelasjonsanalyse: Regnskap vs Avvik", "Test: Samvarierer kontoenes volumstørrelse proporsjonalt med avviksstørrelsen?"))
p11_visuals.extend(get_standard_slicers())
p11_visuals.append(create_kpi_card("Corr Regnskap vs Avvik", "Korrelasjon Regnskap/Avvik", None, 40, 105, 560, 95, 2010))
p11_visuals.append(create_kpi_card("Corr Regnskap vs Budsjett", "Korrelasjon Regnskap/Budsjett", None, 620, 105, 580, 95, 2020))

p11_scat_id = make_id()
p11_visuals.append((p11_scat_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p11_scat_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "scatterChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                            "queryRef": "dim_account.account_name",
                            "nativeQueryRef": "account_name",
                            "active": true
                        }
                    ]
                },
                "X": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } },
                            "queryRef": "_Measures.ERP Regnskap",
                            "nativeQueryRef": "ERP Regnskap"
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } },
                            "queryRef": "_Measures.ERP Avvik",
                            "nativeQueryRef": "ERP Avvik"
                        }
                    ]
                },
                "Tooltips": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett" } }, "queryRef": "_Measures.ERP Budsjett", "nativeQueryRef": "ERP Budsjett" }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Spredningsdiagram: Forbruk (X) mot Avvik (Y)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p11_visuals.append(create_variance_matrix_with_databars("Kontoavstemming & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p11_id,
    "displayName": "11_Scatter_Correlation",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p11_visuals)
all_pages.append(p11_id)

# ==========================================
# PAGE 12: 12_Pareto_80_20
# ==========================================
p12_id = "p12_pareto_curve_0012"
p12_visuals = []
p12_visuals.append(create_header_banner("12 Pareto 80/20 Kostnadsdrivere", "Test: Finner vi 'de få vitale' 20% av kontiene som skaper 80% av merforbruket?"))
p12_visuals.extend(get_standard_slicers())
p12_visuals.append(create_kpi_card("ERP Total Negativ Kostnadsdriver", "Totalt Merforbruk", "ERP RAG Color", 40, 105, 560, 95, 2010))
p12_visuals.append(create_kpi_card("ERP Største Kostnadsdriver Beløp", "Topp Driver", "ERP RAG Color", 620, 105, 580, 95, 2020))

p12_pareto_id = make_id()
p12_visuals.append((p12_pareto_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p12_pareto_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "lineClusteredColumnComboChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                            "queryRef": "dim_account.account_name",
                            "nativeQueryRef": "account_name",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Negativ Kostnadsdriver" } },
                            "queryRef": "_Measures.ERP Negativ Kostnadsdriver",
                            "nativeQueryRef": "ERP Negativ Kostnadsdriver"
                        }
                    ]
                },
                "Y2": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Pareto Kumulativ %" } },
                            "queryRef": "_Measures.ERP Pareto Kumulativ %",
                            "nativeQueryRef": "ERP Pareto Kumulativ %"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Pareto 80/20 Drivere & Kumulativ Merforbrukskurve'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p12_visuals.append(create_variance_matrix_with_databars("Drivere & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p12_id,
    "displayName": "12_Pareto_80_20",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p12_visuals)
all_pages.append(p12_id)

# ==========================================
# PAGE 13: 13_EAC_Runway_Gauge
# ==========================================
p13_id = "p13_runway_gauge_0013"
p13_visuals = []
p13_visuals.append(create_header_banner("13 Helårsramme & Runway Gauge", "Test: Viser gauge-måleren forbrukstakten mer intuitivt for politikere og etatsledelse?"))
p13_visuals.extend(get_standard_slicers())
p13_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 40, 105, 275, 95, 2010))
p13_visuals.append(create_kpi_card("ERP Årsbudsjett", "Årsbudsjett", None, 335, 105, 275, 95, 2020))
p13_visuals.append(create_kpi_card("ERP Forecast EOY", "Helårsprognose EAC", "ERP Forecast EOY Color", 630, 105, 275, 95, 2030))
p13_visuals.append(create_kpi_card("ERP Måneder Igjen", "Restmåneder", None, 925, 105, 275, 95, 2040))

p13_gauge_id = make_id()
p13_visuals.append((p13_gauge_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p13_gauge_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "gauge",
        "query": {
            "queryState": {
                "Y": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap YTD" } }, "queryRef": "_Measures.ERP Regnskap YTD", "nativeQueryRef": "ERP Regnskap YTD" }
                    ]
                },
                "TargetValue": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Årsbudsjett" } }, "queryRef": "_Measures.ERP Årsbudsjett", "nativeQueryRef": "ERP Årsbudsjett" }
                    ]
                },
                "MaxValue": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Forecast EOY" } }, "queryRef": "_Measures.ERP Forecast EOY", "nativeQueryRef": "ERP Forecast EOY" }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Helårsramme & Runway Gauge (Faktisk vs Årsbudsjett vs EAC)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p13_visuals.append(create_variance_matrix_with_databars("Runway Avstemming & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p13_id,
    "displayName": "13_EAC_Runway_Gauge",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p13_visuals)
all_pages.append(p13_id)

# ==========================================
# PAGE 14: 14_AI_Decomp_Tree
# ==========================================
p14_id = "p14_ai_decomp_tree_14"
p14_visuals = []
p14_visuals.append(create_header_banner("14 Power BI AI Dekomponeringstre (Root Cause)", "Test: Kan kunstig intelligens automatisk finne grenene med størst negativt avvik?"))
p14_visuals.extend(get_standard_slicers())
p14_visuals.append(create_kpi_card("ERP Avvik YTD", "Netto Avvik", "ERP RAG Color", 40, 105, 560, 95, 2010))
p14_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 620, 105, 580, 95, 2020))

p14_dt_id = make_id()
p14_visuals.append((p14_dt_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p14_dt_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "decompositionTreeVisual",
        "query": {
            "queryState": {
                "Analyze": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } }, "queryRef": "_Measures.ERP Avvik", "nativeQueryRef": "ERP Avvik" }
                    ]
                },
                "ExplainBy": {
                    "projections": [
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_budget_organization" } }, "Property": "budget_level_2_name" } }, "queryRef": "dim_budget_organization.budget_level_2_name", "nativeQueryRef": "budget_level_2_name", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } }, "queryRef": "dim_account.main_group_name", "nativeQueryRef": "main_group_name", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } }, "queryRef": "dim_account.account_name", "nativeQueryRef": "account_name", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_kostra_function" } }, "Property": "kostra_function_name" } }, "queryRef": "dim_kostra_function.kostra_function_name", "nativeQueryRef": "kostra_function_name", "active": true }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'AI Dekomponeringstre (Interaktiv Rotårsaksanalyse)'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p14_visuals.append(create_variance_matrix_with_databars("Strukturtabell & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p14_id,
    "displayName": "14_AI_Decomp_Tree",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p14_visuals)
all_pages.append(p14_id)

# ==========================================
# PAGE 15: 15_AI_Key_Influencers
# ==========================================
p15_id = "p15_ai_key_influencer"
p15_visuals = []
p15_visuals.append(create_header_banner("15 Power BI AI Nøkkelpåvirkere (Key Influencers)", "Test: Hvilke faktorer (tjenesteområde, kontogruppe, tertial) øker sannsynligheten for sprekk?"))
p15_visuals.extend(get_standard_slicers())
p15_visuals.append(create_kpi_card("ERP Avvik YTD", "Netto Avvik", "ERP RAG Color", 40, 105, 560, 95, 2010))
p15_visuals.append(create_kpi_card("ERP Absolutt Avvik", "Absolutt Avvik", None, 620, 105, 580, 95, 2020))

p15_ki_id = make_id()
p15_visuals.append((p15_ki_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p15_ki_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "keyDriversVisual",
        "query": {
            "queryState": {
                "Analyze": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } }, "queryRef": "_Measures.ERP Avvik", "nativeQueryRef": "ERP Avvik" }
                    ]
                },
                "ExplainBy": {
                    "projections": [
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } }, "queryRef": "dim_account.main_group_name", "nativeQueryRef": "main_group_name", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_kostra_function" } }, "Property": "service_area_name" } }, "queryRef": "dim_kostra_function.service_area_name", "nativeQueryRef": "service_area_name", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "tertial" } }, "queryRef": "dim_date.tertial", "nativeQueryRef": "tertial", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_class_name" } }, "queryRef": "dim_account.account_class_name", "nativeQueryRef": "account_class_name", "active": true }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'AI Nøkkelpåvirkere for Budsjettavvik'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p15_visuals.append(create_variance_matrix_with_databars("Driveroversikt & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p15_id,
    "displayName": "15_AI_Key_Influencers",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p15_visuals)
all_pages.append(p15_id)

# ==========================================
# PAGE 16: 16_AI_QnA_Explorer
# ==========================================
p16_id = "p16_ai_qna_explorer16"
p16_visuals = []
p16_visuals.append(create_header_banner("16 Power BI Q&A Spørsmål & Svar (Naturlig Språk)", "Test: Kan controllere og ledere stille ad-hoc spørsmål på naturlig språk uten å bygge nye rapporter?"))
p16_visuals.extend(get_standard_slicers())
p16_visuals.append(create_kpi_card("ERP Regnskap YTD", "Regnskap YTD", None, 40, 105, 560, 95, 2010))
p16_visuals.append(create_kpi_card("ERP Avvik YTD", "Netto Avvik", "ERP RAG Color", 620, 105, 580, 95, 2020))

p16_qna_id = make_id()
p16_visuals.append((p16_qna_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p16_qna_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "qnaVisual",
        "query": { "queryState": {} },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Power BI Q&A: Still et spørsmål om regnskapet på naturlig språk'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p16_visuals.append(create_variance_matrix_with_databars("Referansetabell & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p16_id,
    "displayName": "16_AI_QnA_Explorer",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p16_visuals)
all_pages.append(p16_id)

# ==========================================
# PAGE 17: 17_Prescription_Bridge
# ==========================================
p17_id = "p17_prescription_br17"
p17_visuals = []
p17_visuals.append(create_header_banner("17 Nullbalanse Tiltaksbro & Innsparingsbane", "Test: Gjør tiltaksbroen det klart hvor mye som må kuttes per måned i P09-P12 (-425k/mnd)?"))
p17_visuals.extend(get_standard_slicers())
p17_visuals.append(create_kpi_card("ERP Forecast EOY Avvik", "Prognoseavvik EAC", "ERP Forecast EOY Color", 40, 105, 360, 95, 2010))
p17_visuals.append(create_kpi_card("ERP Månedlig Tiltaksbehov", "Krav kutt/mnd (P09-P12)", "ERP RAG Color", 420, 105, 360, 95, 2020))
p17_visuals.append(create_kpi_card("ERP Måneder Igjen", "Måneder igjen", None, 800, 105, 400, 95, 2030))

p17_wf_id = make_id()
p17_visuals.append((p17_wf_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p17_wf_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1160, "tabOrder": 2500 },
    "visual": {
        "visualType": "waterfallChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "main_group_name" } },
                            "queryRef": "dim_account.main_group_name",
                            "nativeQueryRef": "main_group_name",
                            "active": true
                        },
                        {
                            "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } },
                            "queryRef": "dim_account.account_name",
                            "nativeQueryRef": "account_name",
                            "active": true
                        }
                    ]
                },
                "Y": {
                    "projections": [
                        {
                            "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Månedlig Tiltaksbehov" } },
                            "queryRef": "_Measures.ERP Månedlig Tiltaksbehov",
                            "nativeQueryRef": "ERP Månedlig Tiltaksbehov"
                        }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Tiltaksbro: Påkrevd Månedlig Innsparing per Hovedgruppe og Konto'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
p17_visuals.append(create_variance_matrix_with_databars("Tiltaksplan & Datastolper"))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p17_id,
    "displayName": "17_Prescription_Bridge",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p17_visuals)
all_pages.append(p17_id)

# ==========================================
# PAGE 18: 18_Data_Quality_Audit
# ==========================================
p18_id = "p18_data_quality_aud"
p18_visuals = []
p18_visuals.append(create_header_banner("18 Datakvalitet, Avstemming & Mapping Health", "Test: Gir revisjonskortet 100% trygghet på at ERP stemmer mot Framsikt og KOSTRA?"))
p18_visuals.extend(get_standard_slicers())
p18_visuals.append(create_kpi_card("Overall Data Quality Status", "Samlet Datakvalitet", "Data Quality Color", 40, 105, 360, 95, 2010))
p18_visuals.append(create_kpi_card("ERP Unmapped Account Rows", "Umappede Kontiader", "ERP RAG Color", 420, 105, 360, 95, 2020))
p18_visuals.append(create_kpi_card("ERP Unmapped Function Rows", "Umappede Funksjonsrader", "ERP RAG Color", 800, 105, 400, 95, 2030))

p18_piv_id = make_id()
p18_visuals.append((p18_piv_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p18_piv_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 840, "width": 1840, "tabOrder": 2500 },
    "visual": {
        "visualType": "pivotTable",
        "query": {
            "queryState": {
                "Rows": {
                    "projections": [
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_code" } }, "queryRef": "dim_account.account_code", "nativeQueryRef": "account_code", "active": true },
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_account" } }, "Property": "account_name" } }, "queryRef": "dim_account.account_name", "nativeQueryRef": "account_name", "active": true }
                    ]
                },
                "Values": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } }, "queryRef": "_Measures.ERP Regnskap", "nativeQueryRef": "ERP Regnskap" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett" } }, "queryRef": "_Measures.ERP Budsjett", "nativeQueryRef": "ERP Budsjett" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } }, "queryRef": "_Measures.ERP Avvik", "nativeQueryRef": "ERP Avvik" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Rader" } }, "queryRef": "_Measures.ERP Rader", "nativeQueryRef": "ERP Rader" }
                    ]
                }
            }
        },
        "objects": {
            "grid": [ { "properties": { "gridVertical": { "expr": { "Literal": { "Value": "false" } } } } } ],
            "columnFormatting": [
                {
                    "properties": {
                        "dataBars": {
                            "positiveColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#16A34A'" } } } } },
                            "negativeColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#DC2626'" } } } } },
                            "axisColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#64748B'" } } } } },
                            "reverseDirection": { "expr": { "Literal": { "Value": "false" } } },
                            "hideText": { "expr": { "Literal": { "Value": "false" } } },
                            "totalMatchingOption": { "expr": { "Literal": { "Value": "1L" } } }
                        }
                    },
                    "selector": { "metadata": "_Measures.ERP Avvik" }
                }
            ]
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Revisjonsavstemming: Kildedata per Konto med Datastolper'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))
save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p18_id,
    "displayName": "18_Data_Quality_Audit",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920
}, p18_visuals)
all_pages.append(p18_id)

# ==========================================
# PAGE 19: 19_Account_Drillthrough
# ==========================================
p19_id = "p19_drillthrough_acc"
p19_visuals = []
p19_visuals.append(create_header_banner("19 Drillthrough Kontodybde", "Test: Gir drillthrough-siden full transaksjonshistorikk og trend for enhver valgt konto?"))
p19_visuals.append(create_kpi_card("Selected Account Drillthrough Title", "Valgt Konto", None, 40, 105, 560, 95, 2010))
p19_visuals.append(create_kpi_card("ERP Avvik YTD", "Kontoens Avvik YTD", "ERP RAG Color", 620, 105, 580, 95, 2020))

# Time series for account
p19_line_id = make_id()
p19_visuals.append((p19_line_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p19_line_id,
    "position": { "x": 40, "y": 210, "z": 2500, "height": 400, "width": 1840, "tabOrder": 2500 },
    "visual": {
        "visualType": "lineChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "month_name" } }, "queryRef": "dim_date.month_name", "nativeQueryRef": "month_name", "active": true }
                    ]
                },
                "Y": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } }, "queryRef": "_Measures.ERP Regnskap", "nativeQueryRef": "ERP Regnskap" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett" } }, "queryRef": "_Measures.ERP Budsjett", "nativeQueryRef": "ERP Budsjett" }
                    ]
                }
            }
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Kontoens Månedlige Forbruk vs Budsjett P01-P12'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))

# Detailed table with databars
p19_tbl_id = make_id()
p19_visuals.append((p19_tbl_id, {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
    "name": p19_tbl_id,
    "position": { "x": 40, "y": 630, "z": 2500, "height": 420, "width": 1840, "tabOrder": 2500 },
    "visual": {
        "visualType": "pivotTable",
        "query": {
            "queryState": {
                "Rows": {
                    "projections": [
                        { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_date" } }, "Property": "year_month" } }, "queryRef": "dim_date.year_month", "nativeQueryRef": "year_month", "active": true }
                    ]
                },
                "Values": {
                    "projections": [
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Budsjett" } }, "queryRef": "_Measures.ERP Budsjett", "nativeQueryRef": "ERP Budsjett" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Regnskap" } }, "queryRef": "_Measures.ERP Regnskap", "nativeQueryRef": "ERP Regnskap" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik" } }, "queryRef": "_Measures.ERP Avvik", "nativeQueryRef": "ERP Avvik" },
                        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "_Measures" } }, "Property": "ERP Avvik %" } }, "queryRef": "_Measures.ERP Avvik %", "nativeQueryRef": "ERP Avvik %" }
                    ]
                }
            }
        },
        "objects": {
            "grid": [ { "properties": { "gridVertical": { "expr": { "Literal": { "Value": "false" } } } } } ],
            "columnFormatting": [
                {
                    "properties": {
                        "dataBars": {
                            "positiveColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#16A34A'" } } } } },
                            "negativeColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#DC2626'" } } } } },
                            "axisColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#64748B'" } } } } },
                            "reverseDirection": { "expr": { "Literal": { "Value": "false" } } },
                            "hideText": { "expr": { "Literal": { "Value": "false" } } },
                            "totalMatchingOption": { "expr": { "Literal": { "Value": "1L" } } }
                        }
                    },
                    "selector": { "metadata": "_Measures.ERP Avvik" }
                }
            ]
        },
        "visualContainerObjects": {
            "title": [ { "properties": { "text": { "expr": { "Literal": { "Value": "'Månedlige Transaksjonslinjer & Datastolper'" } } } } } ]
        },
        "drillFilterOtherVisuals": true
    }
}))

save_page({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": p19_id,
    "displayName": "19_Account_Drillthrough",
    "displayOption": "FitToPage",
    "height": 1080,
    "width": 1920,
    "type": "Drillthrough",
    "filterConfig": {
        "filters": [
            {
                "name": "df_account",
                "field": {
                    "Column": {
                        "Expression": { "SourceRef": { "Entity": "dim_account" } },
                        "Property": "account_name"
                    }
                },
                "type": "Categorical",
                "howCreated": "User"
            }
        ]
    }
}, p19_visuals)
all_pages.append(p19_id)

# ==========================================
# UPDATE pages.json
# ==========================================
with open(pages_json_path, 'w', encoding='utf-8') as f:
    json.dump({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": all_pages,
        "activePageName": p1_id
    }, f, indent=2, ensure_ascii=False)

print(f"Successfully generated all {len(all_pages)} report pages with synced slicers, dynamic RAG, conditional data bars, AI features, and drillthrough!")
