import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find FT_DATA
m = re.search(r'const FT_DATA = \[(.*?)\];\s*const TIME_DATA', text, re.DOTALL)
if m:
    ft_content = m.group(1)
    # Count objects by "id": "ft_
    ids = re.findall(r'"id":\s*"([^"]+)"', ft_content)
    names = re.findall(r'"name":\s*"([^"]+)"', ft_content)
    print(f"FT_DATA found {len(ids)} items.")
    for i, (id_val, name_val) in enumerate(zip(ids, names), 1):
        # check if it has fallback svg
        sub_obj = ft_content.split(f'"id": "{id_val}"')[1].split('},')[0] if f'"id": "{id_val}"' in ft_content else ""
        has_fallback_svg = 'M 35 85 L 70 45 L 105 65 L 140 30 L 170 50' in sub_obj
        has_generic_pbi = 'Bruk ' in sub_obj and 'med filter: fact_erp_finance[location]' in sub_obj
        if has_fallback_svg or has_generic_pbi:
            print(f"  [{i:2d}] {id_val} - {name_val}: fallback_svg={has_fallback_svg}, generic_pbi={has_generic_pbi}")

# Find TIME_DATA
m2 = re.search(r'const TIME_DATA = \[(.*?)\];\s*const BOMILJO', text, re.DOTALL)
if m2:
    time_content = m2.group(1)
    t_ids = re.findall(r'"id":\s*"([^"]+)"', time_content)
    t_names = re.findall(r'"name":\s*"([^"]+)"', time_content)
    print(f"\nTIME_DATA found {len(t_ids)} items.")
    for i, (id_val, name_val) in enumerate(zip(t_ids, t_names), 1):
        sub_obj = time_content.split(f'"id": "{id_val}"')[1].split('},')[0] if f'"id": "{id_val}"' in time_content else ""
        has_fallback_svg = 'M 35 85 L 70 45 L 105 65 L 140 30 L 170 50' in sub_obj
        has_generic_pbi = 'Bruk ' in sub_obj and 'med filter: fact_erp_finance' in sub_obj
        if has_fallback_svg or has_generic_pbi:
            print(f"  [{i:2d}] {id_val} - {name_val}: fallback_svg={has_fallback_svg}, generic_pbi={has_generic_pbi}")
