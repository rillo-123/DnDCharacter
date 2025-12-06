"""Ad-hoc filter to show authoritative vs non-authoritative spell sources."""

from pathlib import Path
import json

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
    print("Spell filtering test:")
    for s in spells:
        name = s.get("name", "UNKNOWN")
        source = s.get("source", "NONE")
        if is_authoritative_source(source):
            shown += 1
            print(f"  ✓ {name:30} ({source})")
        else:
            filtered += 1
            print(f"  ✗ {name:30} ({source}) - FILTERED OUT")

    print(f"\nTotal: {len(spells)}, Shown: {shown}, Filtered: {filtered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
