
"""Check domain bonus spells for a given domain/level against an export JSON."""

from pathlib import Path
import argparse
import json
import sys


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


def _find_default_export(exports_dir: Path) -> Path | None:
    files = sorted(
        (p for p in exports_dir.glob("*.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def get_domain_bonus_spells(domain_name: str, current_level: int):
    domain_key = domain_name.lower().strip() if domain_name else ""
    spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
    bonus_spells = []
    for level in sorted(spells_by_level.keys()):
        if level <= current_level:
            bonus_spells.extend(spells_by_level[level])
    return bonus_spells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="Path to an export JSON. If omitted, uses newest in exports/.")
    parser.add_argument("--exports-dir", type=Path, default=Path("exports"), help="Directory containing export JSON files.")
    parser.add_argument("--domain", default="life", help="Domain name to evaluate (default: life).")
    parser.add_argument("--level", type=int, default=9, help="Character level to use for domain bonus calculation (default: 9).")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]

    exports_dir = args.exports_dir
    if not exports_dir.is_absolute():
        exports_dir = root / exports_dir

    if args.file:
        export_path = args.file
        if not export_path.is_absolute():
            export_path = root / export_path
    else:
        export_path = _find_default_export(exports_dir)
        if export_path is None:
            print(f"No export JSON files found in {exports_dir}")
            return 1

    try:
        data = json.loads(Path(export_path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Failed to load export JSON: {export_path} ({exc})")
        return 1

    domain_spells = get_domain_bonus_spells(args.domain, args.level)
    print(f"{args.domain.title()} domain bonus spells at level {args.level}: {domain_spells}")
    print(f"Total: {len(domain_spells)}")

    spells = data.get("spellcasting", {}).get("prepared", [])
    print(f"\nSpells in character that are domain bonus ({args.domain.title()}):")
    domain_matches = 0
    for s in spells:
        slug = s.get("slug")
        if slug in domain_spells:
            domain_matches += 1
            print(f"  - {s.get('name', 'UNKNOWN')} ({slug})")

    print(f"\nTotal domain bonus spells in prepared list: {domain_matches}")
    print(f"Total prepared spells: {len(spells)}")
    print(f"User-prepared (if {args.domain.title()} domain): {len(spells) - domain_matches}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
