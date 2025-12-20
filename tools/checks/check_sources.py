"""Print source fields for prepared spells from an export JSON."""

from pathlib import Path
import argparse
import json
import sys


def _find_default_export(exports_dir: Path) -> Path | None:
    files = sorted(
        (p for p in exports_dir.glob("*.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="Path to an export JSON. If omitted, uses newest in exports/.")
    parser.add_argument("--exports-dir", type=Path, default=Path("exports"), help="Directory containing export JSON files.")
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

    spells = data.get("spellcasting", {}).get("prepared", [])
    print(f"Spell sources from {export_path}:")
    for s in spells:
        print(f"  {s.get('name', 'UNKNOWN'):30} -> source: {s.get('source', 'NONE')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
