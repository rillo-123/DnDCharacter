"""Print slugs for prepared spells from an export JSON."""

from check_utils import run_check_main


def check_slugs(data, args, export_path) -> int:
    """Check and print spell slugs."""
    spells = data.get("spellcasting", {}).get("prepared", [])
    print(f"All spell slugs from {export_path}:")
    for s in spells:
        print(f"  {s.get('name', 'UNKNOWN'):30} -> {s.get('slug')}")
    return 0


def main() -> int:
    return run_check_main(check_slugs)


if __name__ == "__main__":
    raise SystemExit(main())
