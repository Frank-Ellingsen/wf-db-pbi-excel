import json

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

ft_line = lines[1127].strip()
prefix = 'const FT_DATA = '
if ft_line.startswith(prefix):
    json_str = ft_line[len(prefix):]
    if json_str.endswith(';'):
        json_str = json_str[:-1]
    ft_data = json.loads(json_str)
    print(f"Total FT_DATA items: {len(ft_data)}")
    for i, item in enumerate(ft_data):
        print(f"[{item.get('id')}] {item.get('name')} ({item.get('cat')}) - SVG: {len(item.get('svg', ''))} chars - PBI: {item.get('pbi')[:50]}...")
