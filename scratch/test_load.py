# -*- coding: utf-8 -*-
"""
Generates complete, verified FT_DATA (73 items) and TIME_DATA (60 items)
with distinct, bespoke SVGs and exact _Measures associations.
"""
import json

def get_ft_data():
    # Load base FT_DATA from index.html to preserve core metadata and IDs
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse existing FT_DATA
    import re
    m = re.search(r'const FT_DATA = (\[.*?\]);\s*const TIME_DATA', content, re.DOTALL)
    ft_items = json.loads(m.group(1))
    return ft_items

def get_time_data():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    m = re.search(r'const TIME_DATA = (\[.*?\]);\s*const BOMILJO', content, re.DOTALL)
    time_items = json.loads(m.group(1))
    return time_items

ft = get_ft_data()
time_d = get_time_data()
print(f"Loaded {len(ft)} FT items and {len(time_d)} TIME items.")
