
"""Summarize authoritative vs filtered spells and domain bonuses from an export."""

from pathlib import Path
import json

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
    return any(auth_source in normalized for auth_source in AUTHORITATIVE_SOURCES)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    export_path = root / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
    data = json.loads(export_path.read_text(encoding="utf-8"))
    spells = data.get("spellcasting", {}).get("prepared", [])

    filtered = 0
    shown = 0
    print("Spell filtering summary:")
    for s in spells:
        source = s.get("source", "NONE")
        if is_authoritative_source(source):
            shown += 1
        else:
            filtered += 1

    print(f"Total spells: {len(spells)}")
    print(f"Authoritative (will show): {shown}")
    print(f"Filtered out (A5E, etc): {filtered}")

    # Now check domain spells
    domain = data.get("domain", "") or data.get("identity", {}).get("domain", "")
    print(f"\nCharacter domain: {domain}")

    domain_spells = {
        "life": ["bless", "cure-wounds"],
        "knowledge": ["command", "identify"],
        "trickery": ["charm-person", "disguise-self"],
        "tempest": ["fog-cloud", "thunderwave"],
        "light": ["burning-hands", "faerie-fire"],
        "nature": ["goodberry", "spike_growth"],
        "war": ["divine-favor", "shield-of-faith"],
        "death": ["false-life", "ray-of-enfeeblement"],
        "forge": ["identify", "searing-smite"],
        "grave": ["bane", "false-life"],
        "peace": ["embark-on-a-journey", "protection-from-evil-and-good"],
        "twilight": ["faerie-fire", "sleep"],
    }

    domain_bonus = domain_spells.get(domain.lower(), [])
    print(f"Domain spells: {domain_bonus}")

    domain_count = 0
    for s in spells:
        if s.get("slug") in domain_bonus:
            domain_count += 1
            print(f"  Domain spell: {s.get('name')}")

    print(f"\nDomain bonus spells: {domain_count}")
    print(f"User-prepared (shown - domain): {shown - domain_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
