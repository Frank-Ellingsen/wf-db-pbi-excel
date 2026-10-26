import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')

pages_dir = r'c:\Users\frank\Desktop\WF1\PBI2\pbi-rep-project2.Report\definition\pages'
with open(os.path.join(pages_dir, 'pages.json'), 'r', encoding='utf-8') as f:
    pages_meta = json.load(f)

page_order = pages_meta.get('pageOrder', [])
print(f"Total pages registered in pages.json: {len(page_order)}")
print(f"Active starting page: {pages_meta.get('activePageName')}\n")

total_visuals = 0
for idx, p_id in enumerate(page_order):
    p_path = os.path.join(pages_dir, p_id)
    with open(os.path.join(p_path, 'page.json'), 'r', encoding='utf-8') as pf:
        p_data = json.load(pf)
    vis_dir = os.path.join(p_path, 'visuals')
    v_list = os.listdir(vis_dir) if os.path.exists(vis_dir) else []
    total_visuals += len(v_list)
    p_type = p_data.get('type', 'Standard')
    disp_name = p_data.get('displayName')
    print(f"{idx+1:02d}. {disp_name:<28} | Visuals: {len(v_list):2d} | Type: {p_type}")

print(f"\nTotal visuals across all pages: {total_visuals}")
