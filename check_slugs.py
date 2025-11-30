import json

f = json.load(open('exports/Enwer_Cleric_lvl9_20251126_2147.json'))
spells = f.get('spellcasting', {}).get('prepared', [])

print('All spell slugs:')
for s in spells:
    print(f"  {s.get('name'):30} -> {s.get('slug')}")
