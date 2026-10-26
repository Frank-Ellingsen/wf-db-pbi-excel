import json, re

# Load parsed measures
with open('scratch/measures_summary.json', 'r', encoding='utf-8') as f:
    measures = json.load(f)

print(f"Loaded {len(measures)} measures.")

# Map measures by name for easy lookup
measure_map = {m['name']: m for m in measures}

# Verify some key measures
key_checks = [
    'ERP Regnskap', 'ERP Budsjett', 'ERP Avvik', 'ERP Avvik %',
    'ERP Regnskap Running', 'ERP Regnskap Moving Avg 3M', 'ERP Regnskap MoM',
    'ERP EOY Run Rate', 'EOY Årsbudsjett', 'EOY Run Rate Avvik',
    'EOY Required Correction', 'EOY Required Monthly Correction',
    'Corr Regnskap vs Budsjett', 'Corr Regnskap vs Avvik',
    'ERP Negativ Kostnadsdriver', 'ERP Pareto Kumulativ %', 'ERP Pareto 80 %',
    'ERP Forecast EOY Forbruk %', 'Gauge EOY Target',
    'ERP Mapping %', 'Overall Data Quality Status',
    'ERP RAG', 'ERP RAG Color', 'CF ERP Avvik Bar'
]

missing = [k for k in key_checks if k not in measure_map]
print("Missing key checks:", missing)
print("All key measures present!" if not missing else "Some missing!")
