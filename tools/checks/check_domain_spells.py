
"""Check domain bonus spells for a given domain/level against an export JSON."""

from check_utils import run_check_main


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


def check_domain_spells(data, args, export_path) -> int:
    """Check domain bonus spells."""
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


def main() -> int:
    return run_check_main(check_domain_spells, add_domain_args=True)


if __name__ == "__main__":
    raise SystemExit(main())
