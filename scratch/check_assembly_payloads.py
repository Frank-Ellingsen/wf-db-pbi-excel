# -*- coding: utf-8 -*-
"""
Assembles the complete index.html for WF1 BoMiljo Finansiell Visuell Hub
"""
import json

with open('scratch/ft_data.json', 'r', encoding='utf-8') as f:
    FT_DATA_STR = f.read()

with open('scratch/time_data.json', 'r', encoding='utf-8') as f:
    TIME_DATA_STR = f.read()

with open('scratch/measures_data.json', 'r', encoding='utf-8') as f:
    MEASURES_DATA_STR = f.read()

with open('index.html', 'r', encoding='utf-8') as f:
    orig = f.read()

# Extract BOMILJO and FT_CATS
import re
bomiljo_match = re.search(r'const BOMILJO = (\{.*?\});', orig)
bomiljo_str = bomiljo_match.group(1) if bomiljo_match else "{}"

ft_cats_match = re.search(r'const FT_CATS = (\[.*?\]);', orig)
ft_cats_str = ft_cats_match.group(1) if ft_cats_match else "[]"

print(f"Lengths: FT={len(FT_DATA_STR)}, TIME={len(TIME_DATA_STR)}, MEASURES={len(MEASURES_DATA_STR)}")
