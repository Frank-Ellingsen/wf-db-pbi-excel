# -*- coding: utf-8 -*-
"""
Build complete enriched BoMiljo Financial Visual Hub (index.html)
"""
import json, re, html

# 1. Load measures from scratch/measures_summary.json
with open('scratch/measures_summary.json', 'r', encoding='utf-8') as f:
    MEASURES_RAW = json.load(f)

print(f"Loaded {len(MEASURES_RAW)} measures from _Measures.tmdl")

# 2. Enrich MEASURES_RAW with descriptions, Tufte tips, and recommended visuals
def enrich_measure(m):
    name = m['name']
    folder = m['folder'] or '01 Base'
    expr = m['expression']
    fmt = m['format'] or 'Standard'
    
    # Classify visual pairing
    vis = []
    desc = ""
    
    if 'Regnskap' in name and 'Budsjett' not in name and 'Avvik' not in name:
        vis = ["Column Chart (Magnitude)", "Line Chart", "Area Chart", "Discrete Line Chart"]
        desc = "Grunnleggende bokført forbruk (faktisk regnskap) fra ERP/Framsikt."
    elif 'Budsjett' in name and 'Avvik' not in name:
        vis = ["Bullet Chart", "Bar with Reference Line", "Dual Axis", "Paired Column Chart"]
        desc = "Vedtatt periodisert budsjettramme for enheten."
    elif 'Avvik' in name:
        vis = ["Diverging Bar", "Waterfall Bridge", "Difference from Previous", "Heatmap"]
        desc = "Budsjettavvik (Budsjett - Regnskap). Positivt = mindreforbruk (gunstig), negativt = merforbruk (ugunstig)."
    elif 'MoM' in name or 'Change' in folder:
        vis = ["Diverging MoM", "Difference from Previous", "Slope Graph", "MoM % Columns"]
        desc = "Måned-over-måned endringsrate for å fange akselererende kostnadstrender."
    elif 'Running' in name or 'S-Curve' in name or 'Kumulativ' in name:
        vis = ["Running S-Curve", "Lorenz Curve", "Running Total Area", "Cumulative Runway"]
        desc = "Akkumulert forbruksutvikling over regnskapsåret mot årsrammen."
    elif 'Moving Avg' in name or 'Rolling' in folder:
        vis = ["Moving Average (3M)", "Line + Moving Avg", "Trend Envelope"]
        desc = "Glidende gjennomsnitt som jevner ut sesongtopper (f.eks. ferieavvikling i juli/august)."
    elif 'EOY' in name or 'Forecast' in name or 'Run Rate' in name:
        vis = ["Akkumulert S-Kurve & EAC", "Runway Gauge", "Fan Chart (Projections)", "Prescription Bridge"]
        desc = "Helårsprognose (EAC) og ekstrapolert run-rate for å forutse overskridelser ved årsslutt."
    elif 'Correction' in name or 'Tiltaksbehov' in name or 'Zero Balance' in name:
        vis = ["Nullbalanse Tiltaksbro", "Bullet Chart", "Prescription Action Plan"]
        desc = "Nødvendig månedlig innsparing / tiltakskrav for å lande innenfor vedtatt årsbudsjett."
    elif 'Pareto' in name or 'Driver' in name:
        vis = ["Pareto 80/20 Driveranalyse", "Ordered Bar", "Decomposition Tree"]
        desc = "Identifiserer de 20% av kostnadspostene som skaper 80% av det akkumulerte merforbruket."
    elif 'Corr' in name or 'Correlation' in folder:
        vis = ["Scatterplot", "Connected Scatterplot", "XY Heatmap", "Bubble Chart"]
        desc = "Statistisk samvariasjon (f.eks. overtid vs vikarbyråinnleie)."
    elif 'Mapping' in name or 'Quality' in name or 'Unmapped' in name:
        vis = ["Datakvalitet & Mapping Health", "Barcode Plot", "Status Cards"]
        desc = "Revisjon og dataintegritet: Avdekker uklassifiserte konti eller funksjoner i KOSTRA."
    elif 'RAG' in name or 'Color' in name or 'Symbol' in name:
        vis = ["Executive KPI Belt", "Matrix Sparklines", "Status Grid"]
        desc = "Trafikklys og betinget formatering i tråd med Tufte (dempede farger, grønn/gul/rød)."
    elif 'Rank' in name:
        vis = ["Ordered Bar", "Bump Chart", "Lollipop Chart"]
        desc = "Rangering av kontoposter og KOSTRA-funksjoner etter absolutt avviksstørrelse."
    else:
        vis = ["Standard Controller Card", "Matrix View"]
        desc = "Kontekstuelt styringsmål for BoMiljø og Kristiansand kommune."
        
    return {
        'name': name,
        'folder': folder,
        'format': fmt,
        'expression': expr,
        'description': desc,
        'visuals': vis
    }

MEASURES_ENRICHED = [enrich_measure(m) for m in MEASURES_RAW]
print(f"Enriched {len(MEASURES_ENRICHED)} measures.")

with open('scratch/measures_enriched.json', 'w', encoding='utf-8') as f:
    json.dump(MEASURES_ENRICHED, f, ensure_ascii=False, indent=2)
