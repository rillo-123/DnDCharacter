"""Show is_domain_bonus flags for prepared spells in an export JSON."""

from check_utils import run_check_main


def check_domain_flag(data, args, export_path) -> int:
    """Check and print is_domain_bonus flags."""
    spells = data.get("spellcasting", {}).get("prepared", [])
    print(f"Checking is_domain_bonus flag in {export_path}:")
    for s in spells:
        flag = s.get("is_domain_bonus", "NOT SET")
        print(f"  {s.get('name', 'UNKNOWN'):30} -> is_domain_bonus: {flag}")

    flagged_count = sum(1 for s in spells if s.get("is_domain_bonus"))
    print(f"\nSpells with is_domain_bonus flag: {flagged_count}")
    return 0


def main() -> int:
    return run_check_main(check_domain_flag)


if __name__ == "__main__":
    raise SystemExit(main())
