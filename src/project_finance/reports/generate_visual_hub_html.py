"""
generate_visual_hub_html.py
===========================
Generates a master-level interactive single-page web application (index.html)
implementing:
1. The Financial Times Visual Vocabulary (9 relationship categories, 73 charts)
2. Andy Kriebel's 60 Ways to Visualize Time (Complete 60 taxonomy)
3. Live Interactive Financial Controller Playground (Real WF1 DuckDB data)
4. Project Controller Cheatsheet (EVM, S-Curves, Variances, DAX & Edward Tufte principles)

Zero external dependencies required. Standalone responsive HTML5/CSS3/Vanilla JS.
"""

import json
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(r"C:\Users\frank\Desktop\WF1")
OUTPUT_HTML = PROJECT_ROOT / "index.html"
DB_PATH = PROJECT_ROOT / "db" / "project_finance_powerbi.duckdb"

def get_wf1_data():
    """Extracts live WF1 data from DuckDB for the interactive playground."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Monthly 2024 ERP time series
    monthly = con.execute("""
        SELECT 
            period,
            month,
            month_number,
            ROUND(SUM(budget), 2) as budget,
            ROUND(SUM(actual), 2) as actual,
            ROUND(SUM(budget - actual), 2) as variance,
            ROUND((SUM(budget - actual) / NULLIF(SUM(budget), 0)) * 100, 1) as var_pct
        FROM gold.fact_erp_finance
        GROUP BY period, month, month_number
        ORDER BY month_number
    """).df().to_dict(orient="records")

    # Top 10 account variances
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
        LIMIT 10
    """).df().to_dict(orient="records")

    # KOSTRA functions
    kostra_funcs = con.execute("""
        SELECT 
            kostra_function_id,
            kostra_function_name,
            service_area_name,
            ROUND(SUM(budget_ytd), 2) as budget_ytd,
            ROUND(SUM(actual_ytd), 2) as actual_ytd,
            ROUND(SUM(variance_ytd), 2) as variance_ytd
        FROM gold.fact_framsikt_finance
        GROUP BY kostra_function_id, kostra_function_name, service_area_name
        ORDER BY ABS(SUM(variance_ytd)) DESC
    """).df().to_dict(orient="records")

    con.close()
    return {
        "monthly": monthly,
        "top_accounts": top_accounts,
        "kostra_funcs": kostra_funcs
    }

print("[INFO] Testing DuckDB extraction...")
data = get_wf1_data()
print(f"Loaded: {len(data['monthly'])} months, {len(data['top_accounts'])} accounts, {len(data['kostra_funcs'])} KOSTRA funcs.")
