import json

f = json.load(open('exports/Enwer_Cleric_lvl9_20251126_2147.json'))

print("Full spellcasting block:")
print(json.dumps(f.get('spellcasting', {}), indent=2))
