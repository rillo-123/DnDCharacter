"""Break down prepared spells into cantrips, domain, A5E, and user-prepared lists."""

from pathlib import Path
import json


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json").read_text(encoding="utf-8"))
    spells = data.get("spellcasting", {}).get("prepared", [])

    life_domain = {
        "cure-wounds",
        "bless",
        "lesser-restoration",
        "spiritual-weapon",
        "beacon-of-hope",
        "revivify",
        "guardian-of-faith",
        "death-ward",
        "mass-cure-wounds",
        "raise-dead",
    }

    a5e_spells = {"guiding-bolt-a5e", "healing-word-a5e"}

    print("Spell breakdown:")
    print("=" * 60)

    cantrips = []
    domain_spells = []
    a5e_spells_found = []
    leveled_user_spells = []

    for s in spells:
        slug = s.get("slug", "")
        name = s.get("name", "")
        level = s.get("level", 0)

        if level == 0:
            cantrips.append((name, slug))
        elif slug in a5e_spells:
            a5e_spells_found.append((name, slug))
        elif slug in life_domain:
            domain_spells.append((name, slug))
        else:
            leveled_user_spells.append((name, slug, level))

    print(f"\nCantrips ({len(cantrips)}):")
    for name, slug in cantrips:
        print(f"  - {name} ({slug})")

    print(f"\nLife Domain Bonus Spells ({len(domain_spells)}):")
    for name, slug in domain_spells:
        print(f"  - {name} ({slug})")

    print(f"\nA5E Spells (filtered) ({len(a5e_spells_found)}):")
    for name, slug in a5e_spells_found:
        print(f"  - {name} ({slug})")

    print(f"\nUser-Prepared Leveled Spells ({len(leveled_user_spells)}):")
    for name, slug, level in leveled_user_spells:
        print(f"  - {name} (level {level}) ({slug})")

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Cantrips: {len(cantrips)}")
    print(f"  Domain bonus: {len(domain_spells)}")
    print(f"  A5E (filtered): {len(a5e_spells_found)}")
    print(f"  User-prepared leveled: {len(leveled_user_spells)}")
    print(f"  Total: {len(cantrips) + len(domain_spells) + len(a5e_spells_found) + len(leveled_user_spells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
