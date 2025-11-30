import json

f = json.load(open('exports/Enwer_Cleric_lvl9_20251126_2147.json'))
spells = f.get('spellcasting', {}).get('prepared', [])

print('Checking is_domain_bonus flag:')
for s in spells:
    flag = s.get('is_domain_bonus', 'NOT SET')
    print(f"  {s.get('name'):30} -> is_domain_bonus: {flag}")

flagged_count = sum(1 for s in spells if s.get('is_domain_bonus'))
print(f'\nSpells with is_domain_bonus flag: {flagged_count}')
