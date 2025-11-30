
# Test the filtering logic
AUTHORITATIVE_SOURCES = {
    "phb",  # Player's Handbook
    "xge",  # Xanathar's Guide to Everything
    "xgte",  # Xanathar's Guide to Everything (alternate abbreviation)
    "tcoe",  # Tasha's Cauldron of Everything
    "tce",  # Tasha's Cauldron of Everything (alternate abbreviation)
    "5e core rules",  # Official 5e core rules (equivalent to PHB)
}

def is_authoritative_source(source: str | None) -> bool:
    """Check if spell/item source is from an authoritative D&D 5e book."""
    if not source:
        return False
    # Normalize source name for comparison
    normalized = source.lower().strip()
    # Check exact matches
    if normalized in AUTHORITATIVE_SOURCES:
        return True
    # Check if source contains any authoritative abbreviation or phrase
    for auth_source in AUTHORITATIVE_SOURCES:
        if auth_source in normalized:
            return True
    return False

import json
f = json.load(open('exports/Enwer_Cleric_lvl9_20251126_2147.json'))
spells = f.get('spellcasting', {}).get('prepared', [])

filtered = 0
shown = 0
print('Spell filtering test:')
for s in spells:
    name = s.get('name', 'UNKNOWN')
    source = s.get('source', 'NONE')
    if is_authoritative_source(source):
        shown += 1
        print(f"  ✓ {name:30} ({source})")
    else:
        filtered += 1
        print(f"  ✗ {name:30} ({source}) - FILTERED OUT")

print(f'\nTotal: {len(spells)}, Shown: {shown}, Filtered: {filtered}')
