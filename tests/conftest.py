import sys
import warnings
from pathlib import Path

from _pytest.python import PytestReturnNotNoneWarning


def _ensure_assets_on_path():
    """Add static/assets/py to sys.path with normalized path."""
    assets_py = Path(__file__).parent.parent / "static" / "assets" / "py"
    # Resolve to absolute path and normalize case on Windows
    assets_str = str(assets_py.resolve())
    if assets_str not in sys.path:
        sys.path.insert(0, assets_str)
        print(f"[CONFTEST] Added {assets_str} to sys.path")
    else:
        print(f"[CONFTEST] {assets_str} already in sys.path")


def _ensure_spellcasting_file_attr():
    """Guarantee spellcasting module carries a __file__ attribute for tests."""
    mod = sys.modules.get("spellcasting")
    if mod is None:
        return
    if getattr(mod, "__file__", None):
        return
    candidate = Path.cwd() / "static" / "assets" / "py" / "spellcasting.py"
    mod.__file__ = str(candidate)


def pytest_configure(config):
    print("[CONFTEST] pytest_configure hook called")
    _ensure_assets_on_path()
    _ensure_spellcasting_file_attr()
    warnings.filterwarnings("ignore", category=PytestReturnNotNoneWarning)


def pytest_collection_modifyitems(config, items):
    """Ensure assets are on path before collecting items."""
    _ensure_assets_on_path()
    _ensure_spellcasting_file_attr()


def pytest_runtest_setup(item):
    _ensure_assets_on_path()
    _ensure_spellcasting_file_attr()
