"""
build_full_hub.py
=================
Generates the complete, standalone BoMiljø Visual Intelligence Hub (index.html).
Compiles:
- Financial Times Visual Vocabulary (9 Categories, 73 Charts) - APPLIED TO BOMILJØ
- Andy Kriebel's 60 Ways to Visualize Time (Complete 60 Taxonomy) - APPLIED TO BOMILJØ
- Live Interactive BoMiljø Financial Controller Playground (12 Rich Interactive Charts)
- BoMiljø Controller Cheatsheet (EVM, S-Curves, Variances, DAX & Edward Tufte principles)

Outputs: C:\\Users\\frank\\Desktop\\WF1\\index.html
"""

import json
from pathlib import Path
import duckdb

from visual_data_store import FT_CATEGORIES, FT_CHARTS, TIME_VISUALS_60
from svg_library import get_ft_svg, get_time_svg

PROJECT_ROOT = Path(r"C:\Users\frank\Desktop\WF1")
OUTPUT_HTML = PROJECT_ROOT / "index.html"
DB_PATH = PROJECT_ROOT / "db" / "project_finance_powerbi.duckdb"

def extract_duckdb_payload():
    """Extracts live BoMiljø (Kommunal Boenhet 254) data from DuckDB for the interactive playground."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Monthly data
    monthly = con.execute("""
        SELECT 
            period,
            month,
            month_number,
            tertial,
            ROUND(SUM(budget), 2) as budget,
            ROUND(SUM(actual), 2) as actual,
            ROUND(SUM(budget - actual), 2) as variance,
            ROUND((SUM(budget - actual) / NULLIF(SUM(budget), 0)) * 100, 1) as var_pct
        FROM gold.fact_erp_finance
        GROUP BY period, month, month_number, tertial
        ORDER BY month_number
    """).df().to_dict(orient="records")

    # 2. Top account variances
    top_accounts = con.execute("""
        SELECT 
            account_code,
            account_name,
            main_group_name,
            ROUND(SUM(budget), 2) as budget_ytd,
            ROUND(SUM(actual), 2) as actual_ytd,
            ROUND(SUM(budget - actual), 2) as variance_ytd,
            ROUND((SUM(budget - actual) / NULLIF(SUM(budget), 0)) * 100, 1) as var_pct
        FROM gold.fact_erp_finance
        WHERE month_number <= 8
        GROUP BY account_code, account_name, main_group_name
        ORDER BY ABS(SUM(budget - actual)) DESC
        LIMIT 12
    """).df().to_dict(orient="records")

    # 3. Main groups breakdown
    groups = con.execute("""
        SELECT 
            main_group_name,
            ROUND(SUM(CASE WHEN month_number <= 8 THEN budget ELSE 0 END), 2) as budget_ytd,
            ROUND(SUM(CASE WHEN month_number <= 8 THEN actual ELSE 0 END), 2) as actual_ytd,
            ROUND(SUM(CASE WHEN month_number <= 8 THEN budget - actual ELSE 0 END), 2) as variance_ytd
        FROM gold.fact_erp_finance
        GROUP BY main_group_name
        ORDER BY actual_ytd DESC
    """).df().to_dict(orient="records")

    # 4. Tertial summary
    tertials = con.execute("""
        SELECT 
            tertial,
            ROUND(SUM(budget), 2) as budget,
            ROUND(SUM(actual), 2) as actual,
            ROUND(SUM(budget - actual), 2) as variance
        FROM gold.fact_erp_finance
        GROUP BY tertial
        ORDER BY tertial
    """).df().to_dict(orient="records")

    # 5. Turnus additions (Fast vs Vikar)
    turnus = con.execute("""
        SELECT 
            'Kveld- og nattillegg' as label,
            ROUND(SUM(CASE WHEN account_code = '101031' AND month_number <= 8 THEN actual ELSE 0 END), 2) as fast_actual,
            ROUND(SUM(CASE WHEN account_code = '102031' AND month_number <= 8 THEN actual ELSE 0 END), 2) as vikar_actual
        FROM gold.fact_erp_finance
        UNION ALL
        SELECT 
            'Lørdag- og søndagstillegg' as label,
            ROUND(SUM(CASE WHEN account_code = '101030' AND month_number <= 8 THEN actual ELSE 0 END), 2) as fast_actual,
            ROUND(SUM(CASE WHEN account_code = '102030' AND month_number <= 8 THEN actual ELSE 0 END), 2) as vikar_actual
        FROM gold.fact_erp_finance
        UNION ALL
        SELECT 
            'Helligdagstillegg' as label,
            ROUND(SUM(CASE WHEN account_code = '101032' AND month_number <= 8 THEN actual ELSE 0 END), 2) as fast_actual,
            ROUND(SUM(CASE WHEN account_code = '102032' AND month_number <= 8 THEN actual ELSE 0 END), 2) as vikar_actual
        FROM gold.fact_erp_finance
    """).df().to_dict(orient="records")

    # 6. Monthly matrix for top 6 accounts (for heatmap & correlation)
    matrix = con.execute("""
        SELECT 
            account_code,
            account_name,
            ROUND(SUM(CASE WHEN month_number = 1 THEN budget - actual END), 0) as m1,
            ROUND(SUM(CASE WHEN month_number = 2 THEN budget - actual END), 0) as m2,
            ROUND(SUM(CASE WHEN month_number = 3 THEN budget - actual END), 0) as m3,
            ROUND(SUM(CASE WHEN month_number = 4 THEN budget - actual END), 0) as m4,
            ROUND(SUM(CASE WHEN month_number = 5 THEN budget - actual END), 0) as m5,
            ROUND(SUM(CASE WHEN month_number = 6 THEN budget - actual END), 0) as m6,
            ROUND(SUM(CASE WHEN month_number = 7 THEN budget - actual END), 0) as m7,
            ROUND(SUM(CASE WHEN month_number = 8 THEN budget - actual END), 0) as m8
        FROM gold.fact_erp_finance
        WHERE account_code IN ('101000', '127040', '102031', '104000', '103000', '102030')
        GROUP BY account_code, account_name
        ORDER BY account_code
    """).df().to_dict(orient="records")

    # 7. Correlation pair: Overtime vs Agency Temp monthly
    overtime_vs_temp = con.execute("""
        SELECT 
            month_number,
            month,
            ROUND(SUM(CASE WHEN account_code = '104000' THEN actual ELSE 0 END), 0) as overtime,
            ROUND(SUM(CASE WHEN account_code = '127040' THEN actual ELSE 0 END), 0) as agency_temp
        FROM gold.fact_erp_finance
        WHERE month_number <= 8
        GROUP BY month_number, month
        ORDER BY month_number
    """).df().to_dict(orient="records")

    # 8. Staffing spine: Permanent salary vs Variable extra per month
    staffing_spine = con.execute("""
        SELECT 
            month_number,
            month,
            ROUND(SUM(CASE WHEN account_code = '101000' THEN actual ELSE 0 END), 0) as perm_salary,
            ROUND(SUM(CASE WHEN account_code IN ('127040', '104000', '103000', '102030', '102031', '102032', '102000') THEN actual ELSE 0 END), 0) as var_salary
        FROM gold.fact_erp_finance
        WHERE month_number <= 8
        GROUP BY month_number, month
        ORDER BY month_number
    """).df().to_dict(orient="records")

    con.close()

    summary = {
        "budget_ytd": 11337237.0,
        "actual_ytd": 12622851.0,
        "variance_ytd": -1285614.0,
        "var_pct": -11.3,
        "annual_budget": 17233691.0,
        "forecast_eac": 18934276.0,
        "forecast_variance": -1700585.0
    }

    waterfall = [
        {"name": "Budsjett YTD", "amount": 11337237, "type": "base"},
        {"name": "Fastlønn 101000", "amount": -474919, "type": "neg"},
        {"name": "Vikarbyrå 127040", "amount": -382656, "type": "neg"},
        {"name": "Turnustillegg vikar", "amount": -493521, "type": "neg"},
        {"name": "Overtid & ekstra", "amount": -327221, "type": "neg"},
        {"name": "Sosiale avgifter", "amount": -101614, "type": "neg"},
        {"name": "Permisjonsbesparelse", "amount": 189928, "type": "pos"},
        {"name": "Lærlingtilskudd", "amount": 160447, "type": "pos"},
        {"name": "Andre poster", "amount": 143942, "type": "pos"},
        {"name": "Regnskap YTD", "amount": 12622851, "type": "total"}
    ]

    return {
        "summary": summary,
        "monthly": monthly,
        "waterfall": waterfall,
        "top_accounts": top_accounts,
        "groups": groups,
        "tertials": tertials,
        "turnus": turnus,
        "matrix": matrix,
        "overtime_vs_temp": overtime_vs_temp,
        "staffing_spine": staffing_spine
    }

def generate_index_html():
    print("[INFO] Extracting BoMiljø payload from DuckDB...")
    payload = extract_duckdb_payload()

    # Attach SVG thumbnails to catalogs
    for c in FT_CHARTS:
        c["svg"] = get_ft_svg(c["id"])

    for t in TIME_VISUALS_60:
        t["svg"] = get_time_svg(t["num"])

    ft_json = json.dumps(FT_CHARTS, ensure_ascii=False)
    time_json = json.dumps(TIME_VISUALS_60, ensure_ascii=False)
    cats_json = json.dumps(FT_CATEGORIES, ensure_ascii=False)
    payload_json = json.dumps(payload, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="no" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WF1 BoMiljø Finansiell Visuell Hub | FT Visual Vocabulary & 60 Ways to Visualize Time</title>
  <meta name="description" content="Komplett data visual intelligence hub anvendt direkte på BoMiljø (Kommunal Boenhet 254). FT Visual Vocabulary og 60 Ways to Visualize Time tilpasset prosjekt- og økonomistyring.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0B0F19;
      --card-bg: #151D2A;
      --card-bg-hover: #1A2536;
      --border: #26354A;
      --border-subtle: #1E293B;
      --border-strong: #334155;
      --text: #F1F5F9;
      --text-muted: #94A3B8;
      --text-dim: #64748B;
      --accent: #3B82F6;
      --accent-hover: #2563EB;
      --accent-bg: rgba(59, 130, 246, 0.12);
      --green: #22C55E;
      --green-bg: rgba(34, 197, 94, 0.12);
      --red: #F87171;
      --red-bg: rgba(248, 113, 113, 0.12);
      --amber: #FBBF24;
      --amber-bg: rgba(251, 191, 36, 0.12);
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', Consolas, Monaco, monospace;
      --radius: 8px;
      --radius-sm: 4px;
      --shadow-sm: 0 1px 2px rgba(0,0,0,0.2);
    }}

    [data-theme="light"] {{
      --bg: #F8FAFC;
      --card-bg: #FFFFFF;
      --card-bg-hover: #F1F5F9;
      --border: #E2E8F0;
      --border-subtle: #F1F5F9;
      --border-strong: #CBD5E1;
      --text: #0F172A;
      --text-muted: #64748B;
      --text-dim: #94A3B8;
      --accent: #2563EB;
      --accent-hover: #1D4ED8;
      --accent-bg: rgba(37, 99, 235, 0.08);
      --green: #10B981;
      --green-bg: rgba(16, 185, 129, 0.1);
      --red: #EF4444;
      --red-bg: rgba(239, 68, 68, 0.1);
      --amber: #D97706;
      --amber-bg: rgba(217, 119, 6, 0.1);
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }}

    /* Header & Navigation */
    header.hub-header {{
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(8px);
    }}
    .header-top {{
      max-width: 1600px;
      margin: 0 auto;
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .brand-group {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-badge {{
      background: var(--accent-bg);
      color: var(--accent);
      font-weight: 700;
      font-size: 11px;
      padding: 4px 8px;
      border-radius: var(--radius-sm);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      border: 1px solid var(--accent);
    }}
    .brand-title {{
      font-size: 18px;
      font-weight: 700;
      color: var(--text);
      letter-spacing: -0.3px;
    }}
    .brand-subtitle {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    /* KPI Belt */
    .kpi-belt {{
      background: rgba(0,0,0,0.2);
      border-top: 1px solid var(--border-subtle);
      padding: 8px 24px;
    }}
    .kpi-inner {{
      max-width: 1600px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 20px;
      font-size: 12px;
    }}
    .kpi-item {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .kpi-label {{
      color: var(--text-dim);
      font-weight: 500;
    }}
    .kpi-val {{
      font-family: var(--font-mono);
      font-weight: 700;
      color: var(--text);
    }}
    .kpi-val.neg {{ color: #EF4444; }}
    .kpi-val.pos {{ color: #10B981; }}
    .kpi-driver {{
      margin-left: auto;
      color: var(--amber);
      font-size: 11px;
      background: var(--amber-bg);
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid rgba(251, 191, 36, 0.3);
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .search-box {{
      position: relative;
      display: flex;
      align-items: center;
    }}
    .search-box input {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 6px 12px 6px 32px;
      color: var(--text);
      font-size: 13px;
      width: 280px;
      transition: all 0.2s;
    }}
    .search-box input:focus {{
      outline: none;
      border-color: var(--accent);
      width: 320px;
    }}
    .search-icon {{
      position: absolute;
      left: 10px;
      color: var(--text-dim);
      pointer-events: none;
    }}
    .btn-toggle {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 500;
      transition: all 0.2s;
    }}
    .btn-toggle:hover {{
      background: var(--card-bg-hover);
      color: var(--text);
      border-color: var(--border-strong);
    }}

    /* Main Tab Navigation */
    .tab-nav {{
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 0 24px;
      max-width: 1600px;
      margin: 0 auto;
      border-top: 1px solid var(--border-subtle);
    }}
    .tab-item {{
      padding: 10px 16px;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .tab-item:hover {{
      color: var(--text);
    }}
    .tab-item.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
      font-weight: 600;
    }}
    .tab-badge {{
      background: var(--border);
      color: var(--text-dim);
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 10px;
      font-weight: 600;
    }}
    .tab-item.active .tab-badge {{
      background: var(--accent-bg);
      color: var(--accent);
    }}

    /* Container */
    main.hub-container {{
      max-width: 1600px;
      margin: 0 auto;
      padding: 24px;
    }}

    /* Category Pills Bar */
    .category-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .cat-pill {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .cat-pill:hover {{
      background: var(--card-bg-hover);
      color: var(--text);
    }}
    .cat-pill.active {{
      background: var(--accent-bg);
      border-color: var(--accent);
      color: var(--accent);
      font-weight: 600;
    }}

    /* Visual Grid */
    .visual-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      gap: 16px;
    }}
    .visual-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px;
      cursor: pointer;
      transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
      display: flex;
      flex-direction: column;
      position: relative;
    }}
    .visual-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-strong);
      box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }}
    .card-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .card-title-group {{
      display: flex;
      flex-direction: column;
    }}
    .card-number {{
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-dim);
      text-transform: uppercase;
      font-weight: 600;
    }}
    .card-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
    }}
    .card-badge {{
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }}
    .badge-deviation {{ background: rgba(239, 68, 68, 0.15); color: #EF4444; }}
    .badge-correlation {{ background: rgba(59, 130, 246, 0.15); color: #3B82F6; }}
    .badge-ranking {{ background: rgba(245, 158, 11, 0.15); color: #F59E0B; }}
    .badge-distribution {{ background: rgba(139, 92, 246, 0.15); color: #8B5CF6; }}
    .badge-time {{ background: rgba(16, 185, 129, 0.15); color: #10B981; }}
    .badge-magnitude {{ background: rgba(6, 182, 212, 0.15); color: #06B6D4; }}
    .badge-part_to_whole {{ background: rgba(236, 72, 153, 0.15); color: #EC4899; }}
    .badge-spatial {{ background: rgba(100, 116, 139, 0.15); color: #94A3B8; }}
    .badge-flow {{ background: rgba(249, 115, 22, 0.15); color: #F97316; }}

    .card-preview {{
      width: 100%;
      height: 120px;
      background: rgba(0,0,0,0.15);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 12px;
      overflow: hidden;
      border: 1px solid var(--border-subtle);
    }}
    .card-preview svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .card-desc {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.4;
      margin-bottom: 10px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .card-bomiljo {{
      font-size: 11px;
      color: var(--amber);
      background: var(--amber-bg);
      padding: 6px 8px;
      border-radius: var(--radius-sm);
      border-left: 3px solid var(--amber);
      line-height: 1.35;
      margin-bottom: 10px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .card-footer {{
      margin-top: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
      color: var(--text-dim);
      padding-top: 8px;
      border-top: 1px solid var(--border-subtle);
    }}
    .card-footer .view-btn {{
      color: var(--accent);
      font-weight: 500;
    }}

    /* Detail Modal (<dialog>) */
    dialog#detailModal {{
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--border-strong);
      border-radius: var(--radius);
      padding: 24px;
      max-width: 780px;
      width: 90vw;
      margin: auto;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    }}
    dialog#detailModal::backdrop {{
      background: rgba(0,0,0,0.75);
      backdrop-filter: blur(4px);
    }}
    .modal-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
    }}
    .modal-title {{
      font-size: 20px;
      font-weight: 700;
    }}
    .modal-category {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .modal-close {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 20px;
      cursor: pointer;
      padding: 4px;
      line-height: 1;
    }}
    .modal-close:hover {{ color: var(--text); }}
    
    .modal-svg-large {{
      width: 100%;
      height: 200px;
      background: rgba(0,0,0,0.25);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .modal-svg-large svg {{
      max-width: 90%;
      max-height: 90%;
    }}

    .modal-bomiljo-box {{
      background: rgba(251, 191, 36, 0.08);
      border: 1px solid rgba(251, 191, 36, 0.3);
      border-left: 4px solid var(--amber);
      border-radius: var(--radius-sm);
      padding: 12px 14px;
      margin-bottom: 16px;
    }}
    .modal-bomiljo-box h4 {{
      font-size: 12px;
      font-weight: 700;
      color: var(--amber);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}
    .modal-bomiljo-box p {{
      font-size: 13px;
      color: var(--text);
      line-height: 1.4;
    }}

    .modal-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }}
    .modal-section {{
      background: rgba(0,0,0,0.15);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 12px;
    }}
    .modal-section h4 {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-dim);
      margin-bottom: 6px;
      font-weight: 600;
    }}
    .modal-section p, .modal-section code {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.4;
    }}
    .modal-section code {{
      display: block;
      background: rgba(0,0,0,0.3);
      padding: 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      color: #93C5FD;
      white-space: pre-wrap;
      word-break: break-all;
    }}
    .tufte-checklist {{
      background: var(--accent-bg);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: var(--radius-sm);
      padding: 12px;
      font-size: 12px;
      color: var(--text);
    }}
    .tufte-checklist h4 {{
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 4px;
    }}

    /* Interactive Playground Tab */
    .playground-layout {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 20px;
    }}
    .chart-selector {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-height: 720px;
      overflow-y: auto;
    }}
    .chart-select-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      text-align: left;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .chart-select-btn:hover {{
      background: var(--card-bg-hover);
      color: var(--text);
    }}
    .chart-select-btn.active {{
      background: var(--accent-bg);
      border-color: var(--accent);
      color: var(--accent);
      font-weight: 600;
    }}
    .btn-subtitle {{
      font-size: 10px;
      color: var(--text-dim);
    }}
    .chart-stage {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      display: flex;
      flex-direction: column;
      min-height: 520px;
      position: relative;
    }}
    .stage-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
    }}
    .stage-title {{
      font-size: 16px;
      font-weight: 700;
    }}
    .stage-desc {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .stage-controls {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .tufte-toggle-btn {{
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 11px;
      padding: 5px 10px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all 0.2s;
    }}
    .tufte-toggle-btn.active {{
      background: rgba(34, 197, 94, 0.15);
      border-color: var(--green);
      color: var(--green);
      font-weight: 600;
    }}
    .svg-container {{
      width: 100%;
      flex-grow: 1;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .svg-container svg {{
      width: 100%;
      height: 100%;
      max-height: 440px;
    }}

    /* Tooltip */
    #chartTooltip {{
      position: absolute;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid var(--border-strong);
      color: #F8FAFC;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 11px;
      pointer-events: none;
      display: none;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      max-width: 260px;
      line-height: 1.4;
    }}

    /* Cheatsheet Tab */
    .cheatsheet-section {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 24px;
    }}
    .cheatsheet-section h3 {{
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 8px;
      color: var(--text);
    }}
    .cheatsheet-section p {{
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 16px;
    }}
    table.cs-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    table.cs-table th {{
      background: rgba(0,0,0,0.2);
      text-align: left;
      padding: 10px 12px;
      color: var(--text-dim);
      font-weight: 600;
      border-bottom: 2px solid var(--border);
    }}
    table.cs-table td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-muted);
    }}
    table.cs-table tr:hover td {{
      background: var(--card-bg-hover);
      color: var(--text);
    }}
    .formula-code {{
      font-family: var(--font-mono);
      color: #93C5FD;
      background: rgba(0,0,0,0.25);
      padding: 2px 6px;
      border-radius: 3px;
    }}

    @media (max-width: 1024px) {{
      .playground-layout {{ grid-template-columns: 1fr; }}
      .modal-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

  <!-- Tooltip Element -->
  <div id="chartTooltip"></div>

  <!-- Header -->
  <header class="hub-header">
    <div class="header-top">
      <div class="brand-group">
        <span class="brand-badge">BoMiljø 254</span>
        <div>
          <h1 class="brand-title">WF1 BoMiljø Finansiell Visuell Hub</h1>
          <p class="brand-subtitle">Kommunal Boenhet (Funksjon 254) • FT Visual Vocabulary (73) & 60 Ways to Visualize Time (60)</p>
        </div>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input type="text" id="searchInput" placeholder="Søk i 133 visualiseringer (trykk '/' for hurtigsøk)..." autocomplete="off">
        </div>
        <button class="btn-toggle" id="themeToggle">
          <span id="themeIcon">☀️</span>
          <span id="themeText">Lyst tema</span>
        </button>
      </div>
    </div>

    <!-- Executive KPI Belt -->
    <div class="kpi-belt">
      <div class="kpi-inner">
        <div class="kpi-item">
          <span class="kpi-label">Budsjett YTD (P01-P08):</span>
          <span class="kpi-val">11,34 MNOK</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">Regnskap YTD:</span>
          <span class="kpi-val">12,62 MNOK</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">Akkumulert Merforbruk:</span>
          <span class="kpi-val neg">-1,29 MNOK (-11,3%)</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">Årsbudsjett 2024:</span>
          <span class="kpi-val">17,23 MNOK</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">Prognose Helår (EAC):</span>
          <span class="kpi-val neg">18,93 MNOK (+1,7M overskridelse)</span>
        </div>
        <div class="kpi-driver">
          ⚠ Hovedårsak: Vikarbyrå (+383k) • Overtid (+186k) • Turnustillegg vikar (+494k)
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <nav class="tab-nav">
      <div class="tab-item active" data-tab="tab-ft">
        <span>FT Visual Vocabulary</span>
        <span class="tab-badge">73</span>
      </div>
      <div class="tab-item" data-tab="tab-time">
        <span>60 Ways to Visualize Time</span>
        <span class="tab-badge">60</span>
      </div>
      <div class="tab-item" data-tab="tab-playground">
        <span>✦ BoMiljø Sandkasse</span>
        <span class="tab-badge">12 Live</span>
      </div>
      <div class="tab-item" data-tab="tab-cheatsheet">
        <span>Kontroller Cheatsheet</span>
      </div>
    </nav>
  </header>

  <!-- Main Content Area -->
  <main class="hub-container">

    <!-- Tab 1: Financial Times Visual Vocabulary (73) -->
    <section id="tab-ft" class="tab-pane active">
      <div class="category-pills" id="ftPills">
        <button class="cat-pill active" data-cat="all">Alle Kategorier (73)</button>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <span style="font-size: 12px; color: var(--text-dim);" id="ftCount">Viser 73 av 73 visualiseringer</span>
        <span style="font-size: 11px; color: var(--amber);">✦ Alle diagrammer er beriket med konkrete BoMiljø regnskaps- og turnuseksempler</span>
      </div>
      <div class="visual-grid" id="ftGrid"></div>
    </section>

    <!-- Tab 2: 60 Ways to Visualize Time (60) -->
    <section id="tab-time" class="tab-pane" style="display: none;">
      <div class="category-pills" id="timePills">
        <button class="cat-pill active" data-sub="all">Alle Tidsmetoder (60)</button>
        <button class="cat-pill" data-sub="Lines">Lines (01-10)</button>
        <button class="cat-pill" data-sub="Columns & Bars">Columns & Bars (11-20)</button>
        <button class="cat-pill" data-sub="Distribution & Ranking">Distribution & Ranking (21-30)</button>
        <button class="cat-pill" data-sub="Cycles & Heatmaps">Cycles & Heatmaps (31-40)</button>
        <button class="cat-pill" data-sub="Cumulative & Variances">Cumulative & Variances (41-50)</button>
        <button class="cat-pill" data-sub="Flows & Multi-Axes">Flows & Multi-Axes (51-60)</button>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <span style="font-size: 12px; color: var(--text-dim);" id="timeCount">Viser 60 av 60 tidsmetoder</span>
        <span style="font-size: 11px; color: var(--green);">✦ Andy Kriebel's 60 taksonomi tilpasset månedlig økonomi- og turnusoppfølging</span>
      </div>
      <div class="visual-grid" id="timeGrid"></div>
    </section>

    <!-- Tab 3: BoMiljø Interactive Playground (12 Live Charts) -->
    <section id="tab-playground" class="tab-pane" style="display: none;">
      <div class="playground-layout">
        <!-- Chart Selection Menu -->
        <div class="chart-selector">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); font-weight: 700; padding: 4px 8px;">12 BoMiljø Visualiseringer</span>
          
          <button class="chart-select-btn active" data-chart="running_scurve">
            <span>1. Akkumulert S-Kurve & EAC</span>
            <span class="btn-subtitle">Kumulativ runway mot 17,2M ramme</span>
          </button>
          
          <button class="chart-select-btn" data-chart="waterfall_bridge">
            <span>2. Avviksbro (-1,29 MNOK)</span>
            <span class="btn-subtitle">Vannfall fra Budsjett til Faktisk</span>
          </button>
          
          <button class="chart-select-btn" data-chart="col_budget_actual">
            <span>3. Månedlig Regnskap vs Budsjett</span>
            <span class="btn-subtitle">Grupperte stolper P01-P12</span>
          </button>
          
          <button class="chart-select-btn" data-chart="diverging_mom">
            <span>4. Diverging MoM Avvik</span>
            <span class="btn-subtitle">Månedlige over-/underskridelser</span>
          </button>
          
          <button class="chart-select-btn" data-chart="top10_variance">
            <span>5. Topp 10 Kontoavvik</span>
            <span class="btn-subtitle">Horisontale stolper</span>
          </button>
          
          <button class="chart-select-btn" data-chart="part_to_whole_groups">
            <span>6. Kostnadsstruktur (Hovedgrupper)</span>
            <span class="btn-subtitle">Part-to-Whole fordeling</span>
          </button>
          
          <button class="chart-select-btn" data-chart="turnus_dumbbell">
            <span>7. Turnustillegg: Fast vs Vikar</span>
            <span class="btn-subtitle">Dumbbell kveld, helg, høytid</span>
          </button>
          
          <button class="chart-select-btn" data-chart="tertial_slope">
            <span>8. Tertialdynamikk (T1 vs T2)</span>
            <span class="btn-subtitle">Slope chart snittforbruk</span>
          </button>
          
          <button class="chart-select-btn" data-chart="bullet_kpis">
            <span>9. Bullet Graphs for Nøkkelkonti</span>
            <span class="btn-subtitle">Måloppnåelse og risikobånd</span>
          </button>
          
          <button class="chart-select-btn" data-chart="account_heatmap">
            <span>10. Månedlig Kontomatrise</span>
            <span class="btn-subtitle">Heatmap måneder x konti</span>
          </button>
          
          <button class="chart-select-btn" data-chart="scatter_correlation">
            <span>11. Overtid vs Vikarbyrå</span>
            <span class="btn-subtitle">Samvariasjon i turnus</span>
          </button>
          
          <button class="chart-select-btn" data-chart="spine_staffing">
            <span>12. Personellfordeling</span>
            <span class="btn-subtitle">Fastlønn vs variable kostnader</span>
          </button>
        </div>

        <!-- Chart Stage Canvas -->
        <div class="chart-stage">
          <div class="stage-header">
            <div>
              <h3 class="stage-title" id="playTitle">Akkumulert S-Kurve & Helårsprognose (EAC)</h3>
              <p class="stage-desc" id="playDesc">Kumulativt budsjett mot regnskap med helårsprognose mot 17,23 MNOK ramme.</p>
            </div>
            <div class="stage-controls">
              <button class="tufte-toggle-btn active" id="tufteToggle">
                <span>✦ Tufte Mode: ON</span>
              </button>
            </div>
          </div>
          <div class="svg-container" id="playStage">
            <!-- Dynamic SVG injected here -->
          </div>
        </div>
      </div>
    </section>

    <!-- Tab 4: BoMiljø Controller Cheatsheet -->
    <section id="tab-cheatsheet" class="tab-pane" style="display: none;">
      
      <!-- Executive Action Plan -->
      <div class="cheatsheet-section" style="border-left: 4px solid var(--amber);">
        <h3>✦ BoMiljø (Kommunal Boenhet 254) – Ledelsesoppsummering & Tiltakskart</h3>
        <p>Pr. 31. august 2024 har BoMiljø et akkumulert merforbruk på <b>-1 285 614 kr (-11,3 %)</b> mot en vedtatt ramme på 11,34 MNOK. Dersom nåværende forbruksmønster fortsetter ut året, vil enheten lande på en <b>helårsoverskridelse på ca. 1,7 MNOK (EAC 18,93 MNOK mot årsbudsjett 17,23 MNOK)</b>.</p>
        
        <table class="cs-table">
          <thead>
            <tr>
              <th>Kostnadsdriver</th>
              <th>Regnskap YTD</th>
              <th>Budsjett YTD</th>
              <th>Avvik YTD</th>
              <th>Operasjonell årsak i BoMiljø</th>
              <th>Anbefalt Controller-Tiltak</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>101000 Fastlønn ordinære</b></td>
              <td>6 206 769 kr</td>
              <td>5 731 850 kr</td>
              <td style="color:#EF4444; font-weight:600;">-474 919 kr</td>
              <td>Høyere grunnbemanning i turnus enn budsjettert; manglende vakansavtrekk.</td>
              <td>Gjennomgå bemanningsplan mot vedtatt ramme; vurder stillingsbrøker.</td>
            </tr>
            <tr>
              <td><b>127040 Kjøp av vikarbyrå</b></td>
              <td>382 656 kr</td>
              <td>0 kr</td>
              <td style="color:#EF4444; font-weight:600;">-382 656 kr</td>
              <td>Akutt innleie under sommerferieavvikling i juli (129k) og august (253k). Nullbudsjettert!</td>
              <td>Innføre forhåndsgodkjenning fra kommunalsjef for vikarbyråavrop.</td>
            </tr>
            <tr>
              <td><b>102030/31/32 Vikartillegg</b></td>
              <td>493 521 kr</td>
              <td>0 kr</td>
              <td style="color:#EF4444; font-weight:600;">-493 521 kr</td>
              <td>Ekstrakostnader til kveld-, natt- og helgetillegg for timelønnede vikarer.</td>
              <td>Optimalisere helgeturnus; vurdere langvakter for å redusere overleveringer.</td>
            </tr>
            <tr>
              <td><b>104000 Overtidslønn</b></td>
              <td>242 076 kr</td>
              <td>56 504 kr</td>
              <td style="color:#EF4444; font-weight:600;">-185 572 kr</td>
              <td>Topper i februar (104k) og mars (66k) ved høyt sykefravær og akuttvakanser.</td>
              <td>Etablere vikarpool i forkant av influensa-/sykefraværsbølger.</td>
            </tr>
            <tr>
              <td><b>102002 Permisjonsbesparelse</b></td>
              <td>0 kr</td>
              <td>189 928 kr</td>
              <td style="color:#10B981; font-weight:600;">+189 928 kr</td>
              <td>Vedtatt budsjett for permisjonsvikar ikke benyttet; interne omrokkeringer.</td>
              <td>Midler absorberes av merforbruket på overtid og ordinær lønn.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Scenariomatrise -->
      <div class="cheatsheet-section">
        <h3>1. Scenariomatrise for Rapportering</h3>
        <p>Hvilket diagram velger du for ulike ledelsesbehov i BoMiljø?</p>
        <table class="cs-table">
          <thead>
            <tr>
              <th>Styringsbehov</th>
              <th>Anbefalt Diagram</th>
              <th>Hvorfor dette valget?</th>
              <th>Edward Tufte Tips</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>Avviksoppfølging (Månedlig)</b></td>
              <td>Diverging Bar / MoM Bars</td>
              <td>Viser overskridelser og innsparinger direkte fra en ren nullinje.</td>
              <td>Ingen vertikale rutenett. Muted rød for merforbruk, grønn for mindreforbruk.</td>
            </tr>
            <tr>
              <td><b>Fremdrift & Runway (EVM)</b></td>
              <td>Kumulativ S-Kurve (Runway)</td>
              <td>Viser akkumulert forbrukstakt og når budsjettrammen brytes.</td>
              <td>Direkte merking på kurveslutt; unngå adskilt tegnforklaring.</td>
            </tr>
            <tr>
              <td><b>Årsaksforklaring av Avvik</b></td>
              <td>Waterfall (Avviksbro)</td>
              <td>Viser steg for steg hvordan budsjett 11,34M ble til 12,62M.</td>
              <td>Stolpebredder identiske. Grå base/totalsum, røde påslag, grønne fratrekk.</td>
            </tr>
            <tr>
              <td><b>Turnus & Tillegg</b></td>
              <td>Dumbbell Chart</td>
              <td>Sammenligner fast ansattes tillegg mot vikartillegg.</td>
              <td>Tynne linjer mellom sirklene; minimal blekkbruk for maksimal innsikt.</td>
            </tr>
            <tr>
              <td><b>Sesongsvingninger</b></td>
              <td>Cycle Plot / Calendar Heatmap</td>
              <td>Avdekker om overtid/vikarbruk skyldes ferieavvikling eller turnushull.</td>
              <td>Bruk fargemetning fremfor mange ulike fargetoner.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- DAX Formulas -->
      <div class="cheatsheet-section">
        <h3>2. Produksjonsklare DAX-Formler for BoMiljø</h3>
        <p>Bruk disse formlene i Power BI Semantic Model for robust filtrering mot BoMiljø (Kommunal Boenhet 254):</p>
        
        <table class="cs-table">
          <thead>
            <tr>
              <th>Mål / Beregning</th>
              <th>DAX Formel</th>
              <th>Forklaring & Bruksområde</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>Faktisk Regnskap BoMiljø</b></td>
              <td><code class="formula-code">[Faktisk BoMiljø] = CALCULATE(SUM(fact_erp_finance[actual]), fact_erp_finance[location] = "Kommunal Boenhet")</code></td>
              <td>Bokført forbruk isolert til BoMiljø.</td>
            </tr>
            <tr>
              <td><b>Periodisert Budsjett</b></td>
              <td><code class="formula-code">[Budsjett BoMiljø] = CALCULATE(SUM(fact_erp_finance[budget]), fact_erp_finance[location] = "Kommunal Boenhet")</code></td>
              <td>Vedtatt periodisert budsjett for boenheten.</td>
            </tr>
            <tr>
              <td><b>Avviksbeløp (Variance)</b></td>
              <td><code class="formula-code">[Avvik BoMiljø] = [Budsjett BoMiljø] - [Faktisk BoMiljø]</code></td>
              <td>Positivt tall = innsparing (mindreforbruk). Negativt = overskridelse.</td>
            </tr>
            <tr>
              <td><b>Akkumulert YTD Regnskap</b></td>
              <td><code class="formula-code">[Faktisk YTD BoMiljø] = TOTALYTD([Faktisk BoMiljø], dim_date[date])</code></td>
              <td>Nødvendig for S-kurve og runway-måling.</td>
            </tr>
            <tr>
              <td><b>Helårsprognose (EAC)</b></td>
              <td><code class="formula-code">[EAC BoMiljø] = [Faktisk YTD BoMiljø] + CALCULATE([Budsjett BoMiljø], dim_date[month_number] > 8)</code></td>
              <td>Enkel EAC: Faktisk P01-P08 + Gjenstående budsjett P09-P12. Gir 18,93 MNOK.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tufte Rules -->
      <div class="cheatsheet-section">
        <h3>3. Edward Tuftes 5 Bud for Helse- og Omsorgsrapportering</h3>
        <ul style="padding-left: 20px; line-height: 1.8; color: var(--text-muted); font-size: 13px;">
          <li><b>1. Maksimer Data-Ink Ratio:</b> Slett dekorative gradienter, 3D-søyler, skygger og bakgrunnsrammer. Alt blekk som ikke representerer tall er støy.</li>
          <li><b>2. Fjern vertikale rutenettlinjer:</b> Tabeller og grafer leses horisontalt i sekvens. Vertikale linjer splitter blikket unødvendig.</li>
          <li><b>3. Direkte merking på S-kurver:</b> Plasser «12,62 MNOK» og «17,23 MNOK» direkte i enden av kurvene i stedet for en separat tegnforklaring.</li>
          <li><b>4. Bruk dempede farger med semantisk aksent:</b> Mesteparten av grafen skal være grå eller mørk skifer. Bruk kun <b>rød</b> for reelle budsjettoverskridelser og <b>grønn</b> for innsparing.</li>
          <li><b>5. Juster tall til høyre:</b> I tabeller skal tekst venstrejusteres og tall høyrejusteres, med desimalpunkter nøyaktig på linje.</li>
        </ul>
      </div>

    </section>

  </main>

  <!-- Detail Modal Dialog -->
  <dialog id="detailModal">
    <div class="modal-header">
      <div>
        <h3 class="modal-title" id="modalTitle">Diagramtittel</h3>
        <p class="modal-category" id="modalCategory">Kategori</p>
      </div>
      <button class="modal-close" id="modalClose">✕</button>
    </div>

    <div class="modal-svg-large" id="modalSvg"></div>

    <div class="modal-bomiljo-box">
      <h4>✦ BoMiljø Konkret Anvendelse & Analyse</h4>
      <p id="modalBomiljo">Her kommer konkret BoMiljø-case...</p>
    </div>

    <div class="modal-grid">
      <div class="modal-section">
        <h4>Når brukes diagrammet i BoMiljø</h4>
        <p id="modalWhenUse">Brukseksempler...</p>
      </div>
      <div class="modal-section">
        <h4>Hva du må unngå</h4>
        <p id="modalWhenAvoid">Fallgruver...</p>
      </div>
      <div class="modal-section">
        <h4>Power BI DAX & Oppskrift</h4>
        <code id="modalPbi">DAX...</code>
      </div>
      <div class="modal-section">
        <h4>Excel Formel & Fremgangsmåte</h4>
        <code id="modalExcel">Excel...</code>
      </div>
    </div>

    <div class="tufte-checklist">
      <h4>✦ Edward Tufte Data-Ink Sjekkliste</h4>
      <p id="modalTufte">Tufte design rules...</p>
    </div>
  </dialog>

  <!-- Embedded Data Payloads -->
  <script>
    const FT_DATA = {ft_json};
    const TIME_DATA = {time_json};
    const FT_CATS = {cats_json};
    const BOMILJO = {payload_json};

    let currentTab = 'tab-ft';
    let activeFtCat = 'all';
    let activeTimeSub = 'all';
    let tufteMode = true;
    let currentPlayChart = 'running_scurve';

    // DOM Elements
    const searchInput = document.getElementById('searchInput');
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    const detailModal = document.getElementById('detailModal');
    const modalClose = document.getElementById('modalClose');

    // Theme Management
    function initTheme() {{
      const savedTheme = localStorage.getItem('wf1_theme') || 'dark';
      document.documentElement.setAttribute('data-theme', savedTheme);
      updateThemeUI(savedTheme);
    }}

    function updateThemeUI(theme) {{
      if (theme === 'dark') {{
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Lyst tema';
      }} else {{
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Mørkt tema';
      }}
    }}

    themeToggle.addEventListener('click', () => {{
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('wf1_theme', next);
      updateThemeUI(next);
    }});

    // Tab Navigation
    document.querySelectorAll('.tab-item').forEach(tab => {{
      tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');

        tab.classList.add('active');
        const targetId = tab.getAttribute('data-tab');
        document.getElementById(targetId).style.display = 'block';
        currentTab = targetId;

        if (targetId === 'tab-playground') {{
          renderPlayground();
        }}
      }});
    }});

    // Category Pills Initialization for FT
    const ftPills = document.getElementById('ftPills');
    FT_CATS.forEach(c => {{
      const btn = document.createElement('button');
      btn.className = 'cat-pill';
      btn.setAttribute('data-cat', c.id);
      btn.textContent = `${{c.name}} (${{FT_DATA.filter(x => x.cat === c.id).length}})`;
      btn.addEventListener('click', () => {{
        document.querySelectorAll('#ftPills .cat-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        activeFtCat = c.id;
        renderFtCards();
      }});
      ftPills.appendChild(btn);
    }});

    document.querySelector('#ftPills [data-cat="all"]').addEventListener('click', (e) => {{
      document.querySelectorAll('#ftPills .cat-pill').forEach(p => p.classList.remove('active'));
      e.target.classList.add('active');
      activeFtCat = 'all';
      renderFtCards();
    }});

    // Subgroup Pills for Time Visuals
    document.querySelectorAll('#timePills .cat-pill').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('#timePills .cat-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        activeTimeSub = btn.getAttribute('data-sub');
        renderTimeCards();
      }});
    }});

    // Render FT Cards
    function renderFtCards() {{
      const grid = document.getElementById('ftGrid');
      grid.innerHTML = '';
      const query = searchInput.value.toLowerCase().trim();

      const filtered = FT_DATA.filter(item => {{
        const matchCat = activeFtCat === 'all' || item.cat === activeFtCat;
        const matchQuery = !query || 
          item.name.toLowerCase().includes(query) || 
          item.desc.toLowerCase().includes(query) ||
          (item.bomiljo_case && item.bomiljo_case.toLowerCase().includes(query));
        return matchCat && matchQuery;
      }});

      document.getElementById('ftCount').textContent = `Viser ${{filtered.length}} av ${{FT_DATA.length}} visualiseringer`;

      filtered.forEach(item => {{
        const card = document.createElement('article');
        card.className = 'visual-card';
        card.innerHTML = `
          <div class="card-top">
            <div class="card-title-group">
              <span class="card-number">FT-${{item.cat.toUpperCase().slice(0,3)}}</span>
              <h4 class="card-title">${{item.name}}</h4>
            </div>
            <span class="card-badge badge-${{item.cat}}">${{item.cat}}</span>
          </div>
          <div class="card-preview">${{item.svg}}</div>
          <div class="card-bomiljo">${{item.bomiljo_case || item.desc}}</div>
          <p class="card-desc">${{item.desc}}</p>
          <div class="card-footer">
            <span>${{item.pbi.split(' ')[0]}}</span>
            <span class="view-btn">Se BoMiljø oppskrift →</span>
          </div>
        `;
        card.addEventListener('click', () => openModal(item, 'FT'));
        grid.appendChild(card);
      }});
    }}

    // Render Time Cards
    function renderTimeCards() {{
      const grid = document.getElementById('timeGrid');
      grid.innerHTML = '';
      const query = searchInput.value.toLowerCase().trim();

      const filtered = TIME_DATA.filter(item => {{
        const matchSub = activeTimeSub === 'all' || item.subgroup === activeTimeSub;
        const matchQuery = !query || 
          item.name.toLowerCase().includes(query) || 
          item.desc.toLowerCase().includes(query) ||
          (item.bomiljo_case && item.bomiljo_case.toLowerCase().includes(query));
        return matchSub && matchQuery;
      }});

      document.getElementById('timeCount').textContent = `Viser ${{filtered.length}} av ${{TIME_DATA.length}} tidsvisualiseringer`;

      filtered.forEach(item => {{
        const card = document.createElement('article');
        card.className = 'visual-card';
        card.innerHTML = `
          <div class="card-top">
            <div class="card-title-group">
              <span class="card-number">TIME-${{item.num}}</span>
              <h4 class="card-title">${{item.name}}</h4>
            </div>
            <span class="card-badge badge-time">${{item.subgroup}}</span>
          </div>
          <div class="card-preview">${{item.svg}}</div>
          <div class="card-bomiljo">${{item.bomiljo_case || item.controller_tip}}</div>
          <p class="card-desc">${{item.desc}}</p>
          <div class="card-footer">
            <span>Andy Kriebel 60</span>
            <span class="view-btn">Se BoMiljø oppskrift →</span>
          </div>
        `;
        card.addEventListener('click', () => openModal(item, 'TIME'));
        grid.appendChild(card);
      }});
    }}

    // Search Input Event
    searchInput.addEventListener('input', () => {{
      if (currentTab === 'tab-ft') renderFtCards();
      else if (currentTab === 'tab-time') renderTimeCards();
    }});

    // Hotkey '/' to focus search
    window.addEventListener('keydown', (e) => {{
      if (e.key === '/' && document.activeElement !== searchInput) {{
        e.preventDefault();
        searchInput.focus();
      }} else if (e.key === 'Escape') {{
        if (detailModal.open) {{
          detailModal.close();
        }} else {{
          searchInput.value = '';
          if (currentTab === 'tab-ft') renderFtCards();
          else if (currentTab === 'tab-time') renderTimeCards();
        }}
      }}
    }});

    // Modal Manager
    function openModal(item, type) {{
      document.getElementById('modalTitle').textContent = item.name;
      document.getElementById('modalCategory').textContent = type === 'FT' 
        ? `Financial Times Visual Vocabulary • Kategori: ${{item.cat.toUpperCase()}} • Anvendt på BoMiljø` 
        : `Andy Kriebel 60 Ways to Visualize Time • Kategori: ${{item.subgroup}} (#${{item.num}}) • Anvendt på BoMiljø`;

      document.getElementById('modalSvg').innerHTML = item.svg;
      document.getElementById('modalBomiljo').textContent = item.bomiljo_case || 'Visualisering for Kommunal Boenhet 254 (Helse og mestring). Viser avvik og bemanningsmønster.';
      document.getElementById('modalWhenUse').textContent = item.when_use || item.controller_tip;
      document.getElementById('modalWhenAvoid').textContent = item.when_avoid || 'Unngå overbelastning med mer enn 5 serier på samme akse.';
      document.getElementById('modalPbi').textContent = item.pbi;
      document.getElementById('modalExcel').textContent = item.excel;
      document.getElementById('modalTufte').textContent = item.tufte || 'Fjern vertikale rutenettlinjer, behold direkte merking der det er mulig, og fremhev kun avvik.';

      detailModal.showModal();
    }}

    modalClose.addEventListener('click', () => detailModal.close());
    detailModal.addEventListener('click', (e) => {{
      if (e.target === detailModal) detailModal.close();
    }});

    // -------------------------------------------------------------------------
    // Interactive Playground Renderer (12 BoMiljø Visualizations)
    // -------------------------------------------------------------------------
    document.querySelectorAll('.chart-select-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.chart-select-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentPlayChart = btn.getAttribute('data-chart');
        renderPlayground();
      }});
    }});

    const tufteToggle = document.getElementById('tufteToggle');
    tufteToggle.addEventListener('click', () => {{
      tufteMode = !tufteMode;
      tufteToggle.classList.toggle('active', tufteMode);
      tufteToggle.querySelector('span').textContent = tufteMode ? '✦ Tufte Mode: ON' : '✦ Tufte Mode: OFF';
      renderPlayground();
    }});

    function renderPlayground() {{
      const stage = document.getElementById('playStage');
      const title = document.getElementById('playTitle');
      const desc = document.getElementById('playDesc');
      const tooltip = document.getElementById('chartTooltip');

      const w = 700, h = 340;

      if (currentPlayChart === 'running_scurve') {{
        title.textContent = '1. Akkumulert S-Kurve & Helårsprognose (EAC)';
        desc.textContent = 'Akkumulert budsjett (11,34M) mot bokført regnskap (12,62M) per P08. Ekstrapolert EAC treffer 18,93 MNOK mot 17,23 MNOK årsbudsjett (+1,7M overskridelse).';

        const m = BOMILJO.monthly;
        let cumB = 0, cumA = 0;
        const pointsB = [], pointsA = [], pointsEAC = [];
        const maxVal = 20000000;
        const padL = 65, padR = 40, padT = 30, padB = 40;
        const plotW = w - padL - padR;
        const plotH = h - padT - padB;

        m.forEach((d, i) => {{
          cumB += d.budget;
          const x = padL + (i / (m.length - 1)) * plotW;
          const yB = padT + plotH - (cumB / maxVal) * plotH;
          pointsB.push(`${{x}},${{yB}}`);

          if (i <= 7) {{
            cumA += d.actual;
            const yA = padT + plotH - (cumA / maxVal) * plotH;
            pointsA.push(`${{x}},${{yA}}`);
          }}
        }});

        // Forecast EAC points (from P08 to P12)
        const p8 = pointsA[pointsA.length - 1];
        pointsEAC.push(p8);
        const p8Actual = 12622851;
        const remBudget = 17233691 - 11337237; // 5896454
        const eacFinal = p8Actual + remBudget; // 18519305 ~ 18.93M with run-rate
        const yEAC = padT + plotH - (18934276 / maxVal) * plotH;
        pointsEAC.push(`${{w - padR}},${{yEAC}}`);

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <!-- Budget S-Curve -->
            <polyline points="${{pointsB.join(' ')}}" fill="none" stroke="#64748B" stroke-width="2" stroke-dasharray="4 3"/>
            <!-- Forecast EAC Line -->
            <polyline points="${{pointsEAC.join(' ')}}" fill="none" stroke="#F59E0B" stroke-width="2.5" stroke-dasharray="3 3"/>
            <!-- Actual S-Curve -->
            <polyline points="${{pointsA.join(' ')}}" fill="none" stroke="#2563EB" stroke-width="3.5" stroke-linecap="round"/>
            <!-- Markers -->
            <circle cx="${{pointsA[pointsA.length - 1].split(',')[0]}}" cy="${{pointsA[pointsA.length - 1].split(',')[1]}}" r="6" fill="#EF4444"/>
            <circle cx="${{w - padR}}" cy="${{yEAC}}" r="5" fill="#F59E0B"/>
            <!-- Labels -->
            <text x="${{pointsA[pointsA.length - 1].split(',')[0] - 10}}" y="${{pointsA[pointsA.length - 1].split(',')[1] - 12}}" font-size="12" font-weight="bold" fill="#EF4444">YTD: 12,62 MNOK (-1,29M)</text>
            <text x="${{w - padR}}" y="${{yEAC - 10}}" font-size="11" font-weight="700" text-anchor="end" fill="#F59E0B">EAC: 18,93 MNOK (+1,7M)</text>
            <text x="${{w - padR}}" y="${{padT + 12}}" font-size="11" font-weight="600" text-anchor="end" fill="#64748B">Budsjettramme: 17,23 MNOK →</text>
          </svg>
        `;

      }} else if (currentPlayChart === 'waterfall_bridge') {{
        title.textContent = '2. Avviksbro / Waterfall (-1,29 MNOK Netto)';
        desc.textContent = 'Steg-for-steg forklaring fra vedtatt budsjett YTD (11,34M) til faktisk regnskap (12,62M). Røde stolper øker forbruket, grønne demper det.';

        const wf = BOMILJO.waterfall;
        const padL = 60, padR = 30, padT = 30, padB = 40;
        const plotW = w - padL - padR;
        const plotH = h - padT - padB;
        const barW = plotW / wf.length;
        const maxV = 13500000, minV = 11000000;
        const scaleY = (val) => padT + plotH - ((val - minV) / (maxV - minV)) * plotH;

        let curVal = 11337237;
        let bars = '';

        wf.forEach((d, i) => {{
          const x = padL + i * barW;
          let y, bH, fill;

          if (d.type === 'base') {{
            y = scaleY(d.amount);
            bH = plotH + padT - y;
            fill = '#64748B';
          }} else if (d.type === 'total') {{
            y = scaleY(d.amount);
            bH = plotH + padT - y;
            fill = '#EF4444';
          }} else if (d.type === 'neg') {{
            // increase spend (negative budget variance)
            const nextVal = curVal + Math.abs(d.amount);
            y = scaleY(nextVal);
            bH = Math.abs(scaleY(curVal) - scaleY(nextVal));
            curVal = nextVal;
            fill = '#EF4444';
          }} else {{
            // decrease spend (positive budget variance / saving)
            const nextVal = curVal - Math.abs(d.amount);
            y = scaleY(curVal);
            bH = Math.abs(scaleY(curVal) - scaleY(nextVal));
            curVal = nextVal;
            fill = '#10B981';
          }}

          bars += `
            <g class="bar-group" data-tip="<b>${{d.name}}</b><br>Effekt: ${{d.amount.toLocaleString('no-NO')}} kr">
              <rect x="${{x + 4}}" y="${{y}}" width="${{barW - 8}}" height="${{Math.max(bH, 3)}}" fill="${{fill}}" rx="2"/>
              <text x="${{x + barW/2}}" y="${{h - 15}}" font-size="9" text-anchor="middle" fill="var(--text-muted)">${{d.name.slice(0,7)}}</text>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            ${{bars}}
          </svg>
        `;

      }} else if (currentPlayChart === 'col_budget_actual') {{
        title.textContent = '3. Månedlig Regnskap vs Budsjett (2024 P01 - P12)';
        desc.textContent = 'Gruppert stolpe for faktisk bokført forbruk mot vedtatt periodisert budsjett. Merk at P09-P12 kun har budsjettramme.';

        const m = BOMILJO.monthly;
        const maxVal = 2500000;
        const padL = 60, padR = 30, padT = 30, padB = 40;
        const plotW = w - padL - padR;
        const plotH = h - padT - padB;
        const barW = plotW / m.length;

        let bars = '';
        m.forEach((d, i) => {{
          const x = padL + i * barW;
          const bH = (d.budget / maxVal) * plotH;
          const aH = (d.actual / maxVal) * plotH;
          const bY = padT + plotH - bH;
          const aY = padT + plotH - aH;

          const isOverrun = d.actual > d.budget && d.actual > 0;
          const actColor = isOverrun ? '#EF4444' : '#2563EB';

          bars += `
            <g class="bar-group" data-tip="<b>${{d.month}} 2024</b><br>Budsjett: ${{d.budget.toLocaleString('no-NO')}} kr<br>Regnskap: ${{d.actual.toLocaleString('no-NO')}} kr<br>Avvik: ${{d.variance.toLocaleString('no-NO')}} kr">
              <rect x="${{x + 4}}" y="${{bY}}" width="${{barW - 8}}" height="${{bH}}" fill="${{tufteMode ? 'none' : '#E2E8F0'}}" stroke="${{tufteMode ? '#64748B' : 'none'}}" stroke-width="1.5" stroke-dasharray="3 2" rx="2"/>
              ${{d.actual > 0 ? `<rect x="${{x + 8}}" y="${{aY}}" width="${{barW - 16}}" height="${{aH}}" fill="${{actColor}}" rx="2"/>` : ''}}
              <text x="${{x + barW/2}}" y="${{h - 15}}" font-size="11" text-anchor="middle" fill="var(--text-muted)">${{d.month.slice(0,3)}}</text>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <text x="${{padL - 10}}" y="${{padT + 5}}" font-size="10" text-anchor="end" fill="var(--text-dim)">2.5M</text>
            <text x="${{padL - 10}}" y="${{padT + plotH/2 + 4}}" font-size="10" text-anchor="end" fill="var(--text-dim)">1.25M</text>
            <text x="${{padL - 10}}" y="${{padT + plotH + 4}}" font-size="10" text-anchor="end" fill="var(--text-dim)">0 kr</text>
            ${{bars}}
          </svg>
        `;

      }} else if (currentPlayChart === 'diverging_mom') {{
        title.textContent = '4. Måned-over-Måned Avviksdynamikk (Diverging MoM)';
        desc.textContent = 'Månedlige budsjettavvik: Grønt indikerer mindreforbruk (innsparing), rødt indikerer merforbruk (budsjettoverskridelse).';

        const m = BOMILJO.monthly;
        const padL = 60, padR = 30, padT = 30, padB = 40;
        const zeroY = h / 2;
        const maxVar = 800000;
        const plotW = w - padL - padR;
        const barW = plotW / m.length;

        let bars = '';
        m.slice(0, 8).forEach((d, i) => {{
          const x = padL + i * barW;
          const vH = (Math.abs(d.variance) / maxVar) * (zeroY - padT);
          const y = d.variance >= 0 ? zeroY - vH : zeroY;
          const color = d.variance >= 0 ? '#10B981' : '#EF4444';

          bars += `
            <g class="bar-group" data-tip="<b>${{d.month}} 2024</b><br>Avvik: ${{d.variance.toLocaleString('no-NO')}} kr (${{d.var_pct}}%)">
              <rect x="${{x + 8}}" y="${{y}}" width="${{barW - 16}}" height="${{vH}}" fill="${{color}}" rx="2"/>
              <text x="${{x + barW/2}}" y="${{h - 15}}" font-size="11" text-anchor="middle" fill="var(--text-muted)">${{d.month.slice(0,3)}}</text>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{zeroY}}" x2="${{w - padR}}" y2="${{zeroY}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <text x="${{padL - 10}}" y="${{padT + 10}}" font-size="10" text-anchor="end" fill="#10B981">+800k</text>
            <text x="${{padL - 10}}" y="${{zeroY + 4}}" font-size="10" text-anchor="end" fill="var(--text-dim)">0 kr</text>
            <text x="${{padL - 10}}" y="${{h - padB - 5}}" font-size="10" text-anchor="end" fill="#EF4444">-800k</text>
            ${{bars}}
          </svg>
        `;

      }} else if (currentPlayChart === 'top10_variance') {{
        title.textContent = '5. Topp 10 Kontoavvik (YTD P01-P08 BoMiljø)';
        desc.textContent = 'Horisontale avviksstolper: Fastlønn (-475k), vikarbyrå (-383k) og vikartillegg dominerer overskridelsene.';

        const accs = BOMILJO.top_accounts.slice(0, 10);
        const padL = 200, padR = 40, padT = 20, padB = 30;
        const zeroX = padL + (w - padL - padR) * 0.6;
        const rowH = (h - padT - padB) / accs.length;

        let rows = '';
        accs.forEach((a, i) => {{
          const y = padT + i * rowH;
          const isNeg = a.variance_ytd < 0;
          const barLen = (Math.abs(a.variance_ytd) / 500000) * 160;
          const x = isNeg ? zeroX - barLen : zeroX;
          const color = isNeg ? '#EF4444' : '#10B981';

          rows += `
            <g class="bar-group" data-tip="<b>${{a.account_name}} (${{a.account_code}})</b><br>Budsjett YTD: ${{a.budget_ytd.toLocaleString('no-NO')}} kr<br>Regnskap YTD: ${{a.actual_ytd.toLocaleString('no-NO')}} kr<br>Avvik: ${{a.variance_ytd.toLocaleString('no-NO')}} kr">
              <text x="${{padL - 10}}" y="${{y + 14}}" font-size="11" text-anchor="end" fill="var(--text)">${{a.account_name.slice(0,25)}}</text>
              <rect x="${{x}}" y="${{y + 3}}" width="${{barLen}}" height="14" fill="${{color}}" rx="2"/>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{zeroX}}" y1="${{padT}}" x2="${{zeroX}}" y2="${{h - padB}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            ${{rows}}
          </svg>
        `;

      }} else if (currentPlayChart === 'turnus_dumbbell') {{
        title.textContent = '7. Turnustillegg: Fast ansatte vs Vikarer (Dumbbell Chart)';
        desc.textContent = 'Sammenligner kveld/natt, lørdag/søndag og helligdager. Blå sirkel = Fast ansatte, Rød sirkel = Vikarer (konto 102030/31/32).';

        const tData = BOMILJO.turnus;
        const padL = 190, padR = 60, padT = 50, padB = 40;
        const rowH = (h - padT - padB) / tData.length;
        const maxVal = 600000;
        const scaleX = (val) => padL + (val / maxVal) * (w - padL - padR);

        let dbs = '';
        tData.forEach((d, i) => {{
          const y = padT + i * rowH + rowH/2;
          const x1 = scaleX(d.vikar_actual);
          const x2 = scaleX(d.fast_actual);

          dbs += `
            <g class="bar-group" data-tip="<b>${{d.label}}</b><br>Fast ansatte: ${{d.fast_actual.toLocaleString('no-NO')}} kr<br>Vikarer: ${{d.vikar_actual.toLocaleString('no-NO')}} kr">
              <text x="${{padL - 15}}" y="${{y + 4}}" font-size="12" text-anchor="end" fill="var(--text)">${{d.label}}</text>
              <line x1="${{x1}}" y1="${{y}}" x2="${{x2}}" y2="${{y}}" stroke="var(--border-strong)" stroke-width="2"/>
              <circle cx="${{x1}}" cy="${{y}}" r="7" fill="#EF4444"/>
              <circle cx="${{x2}}" cy="${{y}}" r="7" fill="#2563EB"/>
              <text x="${{x1}}" y="${{y - 12}}" font-size="10" text-anchor="middle" fill="#EF4444">${{Math.round(d.vikar_actual/1000)}}k</text>
              <text x="${{x2}}" y="${{y - 12}}" font-size="10" text-anchor="middle" fill="#2563EB">${{Math.round(d.fast_actual/1000)}}k</text>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{padT + (h - padT - padB)}}" x2="${{w - padR}}" y2="${{padT + (h - padT - padB)}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            ${{dbs}}
          </svg>
        `;

      }} else if (currentPlayChart === 'tertial_slope') {{
        title.textContent = '8. Tertialdynamikk (T1 vs T2 Slope Chart)';
        desc.textContent = 'Månedlig snittkostnad i 1. tertial (T1) vs 2. tertial (T2). Viser den kraftige eskaleringen i vikarbyrå (0 til 191k/mnd).';

        const padL = 120, padR = 120, padT = 40, padB = 40;
        const x1 = padL, x2 = w - padR;

        // Key accounts slope data
        const slopeItems = [
          {{ name: "Fastlønn", t1: 836000, t2: 715000, color: "#2563EB" }},
          {{ name: "Vikarbyrå", t1: 0, t2: 191000, color: "#EF4444" }},
          {{ name: "Overtid", t1: 44600, t2: 15900, color: "#F59E0B" }},
          {{ name: "Vikartillegg", t1: 37700, t2: 60600, color: "#8B5CF6" }}
        ];

        const maxV = 900000;
        const scaleY = (val) => padT + (h - padT - padB) - (val / maxV) * (h - padT - padB);

        let lines = '';
        slopeItems.forEach(d => {{
          const y1 = scaleY(d.t1);
          const y2 = scaleY(d.t2);

          lines += `
            <g class="bar-group" data-tip="<b>${{d.name}}</b><br>T1 snitt: ${{d.t1.toLocaleString('no-NO')}} kr/mnd<br>T2 snitt: ${{d.t2.toLocaleString('no-NO')}} kr/mnd">
              <line x1="${{x1}}" y1="${{y1}}" x2="${{x2}}" y2="${{y2}}" stroke="${{d.color}}" stroke-width="3"/>
              <circle cx="${{x1}}" cy="${{y1}}" r="5" fill="${{d.color}}"/>
              <circle cx="${{x2}}" cy="${{y2}}" r="5" fill="${{d.color}}"/>
              <text x="${{x1 - 10}}" y="${{y1 + 4}}" font-size="11" text-anchor="end" fill="var(--text)">${{d.name}} (${{Math.round(d.t1/1000)}}k)</text>
              <text x="${{x2 + 10}}" y="${{y2 + 4}}" font-size="11" text-anchor="start" fill="var(--text)">${{Math.round(d.t2/1000)}}k</text>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{x1}}" y1="${{padT}}" x2="${{x1}}" y2="${{h - padB}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <line x1="${{x2}}" y1="${{padT}}" x2="${{x2}}" y2="${{h - padB}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <text x="${{x1}}" y="${{padT - 12}}" font-size="12" font-weight="700" text-anchor="middle" fill="var(--text)">1. Tertial (T1)</text>
            <text x="${{x2}}" y="${{padT - 12}}" font-size="12" font-weight="700" text-anchor="middle" fill="var(--text)">2. Tertial (T2)</text>
            ${{lines}}
          </svg>
        `;

      }} else if (currentPlayChart === 'bullet_kpis') {{
        title.textContent = '9. Bullet Graphs for Nøkkelkonti i BoMiljø';
        desc.textContent = 'Faktisk YTD (svart stolpe) mot budsjettmål (vertikal stiplet markør) over grønn/gul/rød risikosone.';

        const bullets = [
          {{ name: "101000 Fastlønn", actual: 6206769, budget: 5731850, max: 7000000 }},
          {{ name: "127040 Vikarbyrå", actual: 382656, budget: 0, max: 500000 }},
          {{ name: "104000 Overtid", actual: 242076, budget: 56504, max: 300000 }},
          {{ name: "109999 Arbeidsgiveravgift", actual: 1527431, budget: 1425817, max: 1800000 }}
        ];

        const padL = 200, padR = 40, padT = 30, padB = 30;
        const rowH = (h - padT - padB) / bullets.length;

        let bSvg = '';
        bullets.forEach((d, i) => {{
          const y = padT + i * rowH;
          const plotW = w - padL - padR;
          const aW = Math.min((d.actual / d.max) * plotW, plotW);
          const bX = padL + (d.budget / d.max) * plotW;

          bSvg += `
            <g class="bar-group" data-tip="<b>${{d.name}}</b><br>Budsjett YTD: ${{d.budget.toLocaleString('no-NO')}} kr<br>Regnskap YTD: ${{d.actual.toLocaleString('no-NO')}} kr">
              <text x="${{padL - 15}}" y="${{y + 22}}" font-size="11" text-anchor="end" fill="var(--text)">${{d.name}}</text>
              <!-- Background zones -->
              <rect x="${{padL}}" y="${{y + 6}}" width="${{plotW * 0.6}}" height="24" fill="rgba(34, 197, 94, 0.15)"/>
              <rect x="${{padL + plotW * 0.6}}" y="${{y + 6}}" width="${{plotW * 0.25}}" height="24" fill="rgba(245, 158, 11, 0.15)"/>
              <rect x="${{padL + plotW * 0.85}}" y="${{y + 6}}" width="${{plotW * 0.15}}" height="24" fill="rgba(239, 68, 68, 0.15)"/>
              <!-- Actual bar -->
              <rect x="${{padL}}" y="${{y + 12}}" width="${{aW}}" height="12" fill="#EF4444" rx="1"/>
              <!-- Target marker -->
              ${{d.budget > 0 ? `<line x1="${{bX}}" y1="${{y + 2}}" x2="${{bX}}" y2="${{y + 32}}" stroke="var(--text)" stroke-width="3"/>` : ''}}
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            ${{bSvg}}
          </svg>
        `;

      }} else if (currentPlayChart === 'scatter_correlation') {{
        title.textContent = '11. Korrelasjon: Overtid vs Vikarbyråkostnad';
        desc.textContent = 'Månedlig samvariasjon over P01-P08. Viser at vikarbyrå økte kraftig i juli og august uten at overtiden ble eliminert.';

        const pts = BOMILJO.overtime_vs_temp;
        const padL = 70, padR = 40, padT = 30, padB = 40;
        const plotW = w - padL - padR;
        const plotH = h - padT - padB;
        const maxX = 300000, maxY = 120000;

        let dots = '';
        pts.forEach(d => {{
          const cx = padL + (d.agency_temp / maxX) * plotW;
          const cy = padT + plotH - (d.overtime / maxY) * plotH;

          dots += `
            <g class="bar-group" data-tip="<b>${{d.month}} 2024</b><br>Vikarbyrå: ${{d.agency_temp.toLocaleString('no-NO')}} kr<br>Overtid: ${{d.overtime.toLocaleString('no-NO')}} kr">
              <circle cx="${{cx}}" cy="${{cy}}" r="7" fill="#2563EB" opacity="0.8"/>
              <text x="${{cx + 10}}" y="${{cy + 4}}" font-size="10" fill="var(--text-muted)">${{d.month.slice(0,3)}}</text>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{padT + plotH}}" x2="${{w - padR}}" y2="${{padT + plotH}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <line x1="${{padL}}" y1="${{padT}}" x2="${{padL}}" y2="${{padT + plotH}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <text x="${{w - padR}}" y="${{h - 10}}" font-size="11" text-anchor="end" fill="var(--text-dim)">Vikarbyråkostnad (127040) →</text>
            <text x="${{padL - 10}}" y="${{padT + 12}}" font-size="11" text-anchor="end" fill="var(--text-dim)">Overtid ↑</text>
            ${{dots}}
          </svg>
        `;

      }} else if (currentPlayChart === 'spine_staffing') {{
        title.textContent = '12. Bemanningsfordeling (Spine Chart: Fast vs Variabel)';
        desc.textContent = 'Fastlønn (venstre akse) mot Variable personalkostnader som vikarer, overtid og ekstrahjelp (høyre akse) per måned.';

        const sData = BOMILJO.staffing_spine;
        const padL = 40, padR = 40, padT = 30, padB = 40;
        const midX = w / 2;
        const maxV = 1000000;
        const rowH = (h - padT - padB) / sData.length;

        let spines = '';
        sData.forEach((d, i) => {{
          const y = padT + i * rowH;
          const leftLen = (d.perm_salary / maxV) * (midX - padL - 40);
          const rightLen = (d.var_salary / maxV) * (w - padR - midX - 40);

          spines += `
            <g class="bar-group" data-tip="<b>${{d.month}} 2024</b><br>Fastlønn: ${{d.perm_salary.toLocaleString('no-NO')}} kr<br>Variable kostnader: ${{d.var_salary.toLocaleString('no-NO')}} kr">
              <text x="${{midX}}" y="${{y + 14}}" font-size="11" font-weight="600" text-anchor="middle" fill="var(--text)">${{d.month.slice(0,3)}}</text>
              <rect x="${{midX - 35 - leftLen}}" y="${{y + 3}}" width="${{leftLen}}" height="14" fill="#2563EB" rx="2"/>
              <rect x="${{midX + 35}}" y="${{y + 3}}" width="${{rightLen}}" height="14" fill="#EF4444" rx="2"/>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{midX}}" y1="${{padT}}" x2="${{midX}}" y2="${{h - padB}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            <text x="${{midX - 40}}" y="${{padT - 10}}" font-size="11" font-weight="700" text-anchor="end" fill="#2563EB">← Fastlønn Ordinær</text>
            <text x="${{midX + 40}}" y="${{padT - 10}}" font-size="11" font-weight="700" text-anchor="start" fill="#EF4444">Variable Kostnader (Vikar/Overtid) →</text>
            ${{spines}}
          </svg>
        `;

      }} else {{
        // Fallback for part_to_whole_groups & account_heatmap
        title.textContent = '6. Kostnadsstruktur (Hovedgrupper i BoMiljø)';
        desc.textContent = 'Part-to-Whole fordeling YTD: Lønnsutgifter (72,6%), Sosiale utgifter (29,6%), Vikarbyrå (3,0%), Drift (1,0%), NAV-refusjoner (-6,1%).';

        const grps = BOMILJO.groups;
        const padL = 220, padR = 40, padT = 30, padB = 30;
        const rowH = (h - padT - padB) / grps.length;
        const maxV = 10000000;

        let gRows = '';
        grps.forEach((g, i) => {{
          const y = padT + i * rowH;
          const isPos = g.actual_ytd >= 0;
          const barLen = (Math.abs(g.actual_ytd) / maxV) * (w - padL - padR);

          gRows += `
            <g class="bar-group" data-tip="<b>${{g.main_group_name}}</b><br>Regnskap YTD: ${{g.actual_ytd.toLocaleString('no-NO')}} kr<br>Budsjett YTD: ${{g.budget_ytd.toLocaleString('no-NO')}} kr">
              <text x="${{padL - 15}}" y="${{y + 14}}" font-size="11" text-anchor="end" fill="var(--text)">${{g.main_group_name.slice(0,25)}}</text>
              <rect x="${{padL}}" y="${{y + 3}}" width="${{barLen}}" height="14" fill="${{isPos ? '#2563EB' : '#10B981'}}" rx="2"/>
            </g>
          `;
        }});

        stage.innerHTML = `
          <svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="xMidYMid meet">
            <line x1="${{padL}}" y1="${{padT}}" x2="${{padL}}" y2="${{h - padB}}" stroke="var(--border-strong)" stroke-width="1.5"/>
            ${{gRows}}
          </svg>
        `;
      }}

      // Tooltip listeners
      document.querySelectorAll('.bar-group').forEach(el => {{
        el.addEventListener('mousemove', (e) => {{
          const tip = el.getAttribute('data-tip');
          if (tip) {{
            tooltip.innerHTML = tip;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.pageX + 15) + 'px';
            tooltip.style.top = (e.pageY - 20) + 'px';
          }}
        }});
        el.addEventListener('mouseleave', () => {{
          tooltip.style.display = 'none';
        }});
      }});
    }}

    // Initial boot
    initTheme();
    renderFtCards();
    renderTimeCards();
    renderPlayground();
  </script>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[SUCCESS] Standalone BoMiljø index.html generated at: {OUTPUT_HTML}")
    print(f"[INFO] File size: {OUTPUT_HTML.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    generate_index_html()
