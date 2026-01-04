"""Print source fields for prepared spells from an export JSON."""

from check_utils import run_check_main


def check_sources(data, args, export_path) -> int:
    """Check and print spell sources."""
    spells = data.get("spellcasting", {}).get("prepared", [])
    print(f"Spell sources from {export_path}:")
    for s in spells:
        print(f"  {s.get('name', 'UNKNOWN'):30} -> source: {s.get('source', 'NONE')}")
    return 0


def main() -> int:
    return run_check_main(check_sources)


if __name__ == "__main__":
    raise SystemExit(main())
