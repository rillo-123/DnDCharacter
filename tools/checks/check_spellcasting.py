"""Dump the spellcasting block from an export JSON."""

import json
from check_utils import run_check_main


def check_spellcasting(data, args, export_path) -> int:
    """Dump the spellcasting block."""
    print(f"Full spellcasting block from {export_path}:")
    print(json.dumps(data.get("spellcasting", {}), indent=2))
    return 0


def main() -> int:
    return run_check_main(check_spellcasting)


if __name__ == "__main__":
	raise SystemExit(main())
