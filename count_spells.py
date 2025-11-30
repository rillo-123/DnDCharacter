
# Test the filtering logic
AUTHORITATIVE_SOURCES = {
    "phb",
    "xge",
    "xgte",
    "tcoe",
    "tce",
    "5e core rules",
}

def is_authoritative_source(source: str | None) -> bool:
    if not source:
        return False
    normalized = source.lower().strip()
    if normalized in AUTHORITATIVE_SOURCES:
        return True
    for auth_source in AUTHORITATIVE_SOURCES:
        if auth_source in normalized:
            return True
    return False

import json
f = json.load(open('exports/Enwer_Cleric_lvl9_20251126_2147.json'))
spells = f.get('spellcasting', {}).get('prepared', [])

filtered = 0
shown = 0
print('Spell filtering summary:')
for s in spells:
    name = s.get('name', 'UNKNOWN')
    source = s.get('source', 'NONE')
    if is_authoritative_source(source):
        shown += 1
    else:
        filtered += 1

print(f'Total spells: {len(spells)}')
print(f'Authoritative (will show): {shown}')
print(f'Filtered out (A5E, etc): {filtered}')

# Now check domain spells
spellcasting = f.get('spellcasting', {})
domain = f.get('domain', '')
print(f'\nCharacter domain: {domain}')

# Get domain spells from code (we need to hardcode them here for testing)
domain_spells = {
    "life": ["bless", "cure-wounds"],
    "knowledge": ["command", "identify"],
    "trickery": ["charm-person", "disguise-self"],
    "tempest": ["fog-cloud", "thunderwave"],
    "light": ["burning-hands", "faerie-fire"],
    "nature": ["goodberry", "spike-growth"],
    "war": ["divine-favor", "shield-of-faith"],
    "death": ["false-life", "ray-of-enfeeblement"],
    "forge": ["identify", "searing-smite"],
    "grave": ["bane", "false-life"],
    "peace": ["embark-on-a-journey", "protection-from-evil-and-good"],
    "twilight": ["faerie-fire", "sleep"],
}

domain_bonus = domain_spells.get(domain.lower(), [])
print(f'Domain spells: {domain_bonus}')

# Count domain spells in prepared
domain_count = 0
for s in spells:
    if s.get('slug') in domain_bonus:
        domain_count += 1
        print(f'  Domain spell: {s.get("name")}')

print(f'\nDomain bonus spells: {domain_count}')
print(f'User-prepared (shown - domain): {shown - domain_count}')
