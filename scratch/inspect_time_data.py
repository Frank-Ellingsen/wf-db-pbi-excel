import json

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

time_line = lines[1128].strip()
prefix = 'const TIME_DATA = '
if time_line.startswith(prefix):
    json_str = time_line[len(prefix):]
    if json_str.endswith(';'):
        json_str = json_str[:-1]
    time_data = json.loads(json_str)
    print(f"Total TIME_DATA items: {len(time_data)}")
    for i, item in enumerate(time_data):
        has_generic_pbi = 'Bruk ' in item.get('pbi', '') or 'fact_erp_finance' in item.get('pbi', '')
        print(f"[{item.get('num')}] {item.get('name')} ({item.get('subgroup')}): PBI DAX: {item.get('pbi')[:60]}... SVG len: {len(item.get('svg', ''))}")
