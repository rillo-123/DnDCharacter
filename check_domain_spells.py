
# Domain bonus spells for Life domain
DOMAIN_BONUS_SPELLS = {
    "life": {
        1: ["cure-wounds", "bless"],
        3: ["lesser-restoration", "spiritual-weapon"],
        5: ["beacon-of-hope", "revivify"],
        7: ["guardian-of-faith", "death-ward"],
        9: ["mass-cure-wounds", "raise-dead"],
    },
}

def get_domain_bonus_spells(domain_name: str, current_level: int):
    domain_key = domain_name.lower().strip() if domain_name else ""
    spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
    
    bonus_spells = []
    for level in sorted(spells_by_level.keys()):
        if level <= current_level:
            bonus_spells.extend(spells_by_level[level])
    return bonus_spells

# For Life domain at level 9
life_domain_spells = get_domain_bonus_spells("life", 9)
print(f"Life domain bonus spells at level 9: {life_domain_spells}")
print(f"Total: {len(life_domain_spells)}")

# Now check what spells your character has
import json
f = json.load(open('exports/Enwer_Cleric_lvl9_20251126_2147.json'))
spells = f.get('spellcasting', {}).get('prepared', [])

print('\nSpells in your character that are domain bonus (Life domain):')
domain_matches = 0
for s in spells:
    slug = s.get('slug')
    if slug in life_domain_spells:
        domain_matches += 1
        print(f"  - {s.get('name')} ({slug})")

print(f'\nTotal domain bonus spells in your prepared list: {domain_matches}')
print(f'Total prepared spells: {len(spells)}')
print(f'User-prepared (if Life domain): {len(spells) - domain_matches}')
