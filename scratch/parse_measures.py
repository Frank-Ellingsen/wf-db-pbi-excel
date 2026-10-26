import re, json

with open('powerbi/pbi-rep-project.SemanticModel/definition/tables/_Measures.tmdl', 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# Pattern for measures
# measure 'Name' = ...
#    formatString: ...
#    displayFolder: ...
measure_blocks = re.split(r'\n\s*measure\s+', text)
parsed_measures = []

for block in measure_blocks[1:]:
    lines = block.strip().split('\n')
    first_line = lines[0]
    name_match = re.match(r"'([^']+)'\s*=\s*(.*)", first_line)
    if not name_match:
        continue
    m_name = name_match.group(1)
    expr_start = name_match.group(2)
    
    folder = ""
    format_str = ""
    expr_lines = []
    if expr_start:
        expr_lines.append(expr_start)
        
    for l in lines[1:]:
        l_strip = l.strip()
        if l_strip.startswith('displayFolder:'):
            folder = l_strip.replace('displayFolder:', '').strip()
        elif l_strip.startswith('formatString:'):
            format_str = l_strip.replace('formatString:', '').strip()
        elif l_strip.startswith('lineageTag:'):
            pass
        else:
            expr_lines.append(l)
            
    parsed_measures.append({
        'name': m_name,
        'folder': folder,
        'format': format_str,
        'expression': '\n'.join(expr_lines).strip()
    })

print(f"Parsed {len(parsed_measures)} measures successfully.")
folders = {}
for m in parsed_measures:
    f = m['folder'] or 'No Folder'
    folders[f] = folders.get(f, 0) + 1

for f, count in sorted(folders.items()):
    print(f"  {f}: {count} measures")

with open('scratch/measures_summary.json', 'w', encoding='utf-8') as out:
    json.dump(parsed_measures, out, ensure_ascii=False, indent=2)
