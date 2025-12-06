"""Test if exec() approach works for loading modules."""

from pathlib import Path
from types import ModuleType
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    # Test 1: Can we load a file and exec it?
    with open(root / "assets" / "py" / "spell_data.py", encoding="utf-8") as f:
        source = f.read()

    spell_data = ModuleType("spell_data")
    exec(source, spell_data.__dict__)
    sys.modules["spell_data"] = spell_data

    print("✓ spell_data loaded via exec()")
    print(f"  Has SPELL_CLASS_SYNONYMS: {hasattr(spell_data, 'SPELL_CLASS_SYNONYMS')}")

    # Test 2: Now load spellcasting which imports spell_data
    with open(root / "assets" / "py" / "spellcasting.py", encoding="utf-8") as f:
        source = f.read()

    spellcasting = ModuleType("spellcasting")
    try:
        exec(source, spellcasting.__dict__)
        print("✓ spellcasting loaded via exec()")
        print(f"  Has SpellcastingManager: {hasattr(spellcasting, 'SpellcastingManager')}")
    except ImportError as e:
        print(f"✗ spellcasting exec failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
