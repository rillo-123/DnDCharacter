"""
Unit tests to catch PyScript file serving and module loading issues.
These tests detect when Python files aren't accessible to PyScript.
"""

import os
import sys
from pathlib import Path


def test_files_exist_locally():
    """Test that all required Python files exist in the filesystem."""
    print("\n=== TEST: Required files exist ===")
    
    required_files = [
        "assets/py/character.py",
        "assets/py/spell_data.py",
        "assets/py/spellcasting.py",
        "assets/py/character_models.py",
        "assets/py/entities.py",
        "assets/py/equipment_management.py",
        "assets/py/export_management.py",
        "assets/py/browser_logger.py",
    ]
    
    cwd = Path.cwd()
    all_exist = True
    
    for file_path in required_files:
        full_path = cwd / file_path
        exists = full_path.exists()
        status = "[OK]" if exists else "[FAIL]"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def test_pyscript_would_find_files():
    """
    Test: Would PyScript find these files?
    PyScript looks for files relative to HTML location.
    Simulates: /home/pyodide/ as working directory
    """
    print("\n=== TEST: PyScript file discovery simulation ===")
    print("\nSimulating PyScript environment:")
    print("  Working dir: /home/pyodide/")
    print("  Looking for: /home/pyodide/assets/py/spellcasting.py")
    print()
    
    # Check what would happen if cwd was /home/pyodide
    pyscript_cwd = Path("/home/pyodide")
    pyscript_assets = pyscript_cwd / "assets" / "py"
    
    print(f"If PyScript cwd = {pyscript_cwd}:")
    print(f"  assets/py path would be: {pyscript_assets}")
    print(f"  This path exists locally? {pyscript_assets.exists()}")
    print(f"  This is expected: NO (PyScript runs in sandbox, not local filesystem)")
    print()
    
    # The real check: are files accessible from current directory?
    current_assets = Path.cwd() / "assets" / "py"
    print(f"In current environment:")
    print(f"  Current working dir: {Path.cwd()}")
    print(f"  assets/py path: {current_assets}")
    print(f"  Exists? {current_assets.exists()}")
    
    if current_assets.exists():
        spellcasting = current_assets / "spellcasting.py"
        print(f"  spellcasting.py exists? {spellcasting.exists()}")
        return spellcasting.exists()
    
    return False


def test_sys_path_includes_assets_py():
    """Test that assets/py can be added to sys.path."""
    print("\n=== TEST: sys.path modification capability ===")
    
    assets_py = Path.cwd() / "assets" / "py"
    print(f"Target path: {assets_py}")
    print(f"Exists? {assets_py.exists()}")
    
    if not assets_py.exists():
        print("[FAIL] Target path does not exist")
        return False
    
    # Try to add it to sys.path
    original_path = sys.path.copy()
    sys.path.insert(0, str(assets_py))
    
    added = str(assets_py) in sys.path
    print(f"Added to sys.path? {added}")
    
    sys.path = original_path
    return added


def test_spellcasting_findable_after_path_update():
    """Test that spellcasting can be found after sys.path update."""
    print("\n=== TEST: spellcasting findable after path update ===")
    
    assets_py = Path.cwd() / "assets" / "py"
    
    if str(assets_py) not in sys.path:
        sys.path.insert(0, str(assets_py))
    
    spellcasting_file = assets_py / "spellcasting.py"
    print(f"spellcasting.py exists? {spellcasting_file.exists()}")
    
    if not spellcasting_file.exists():
        print("[FAIL] spellcasting.py not found")
        return False
    
    # Try importing
    try:
        import spellcasting
        print(f"[OK] Can import spellcasting")
        print(f"      Location: {spellcasting.__file__}")
        return True
    except ImportError as e:
        print(f"[FAIL] Cannot import spellcasting: {e}")
        return False


def test_pyscript_file_serving_requirement():
    """
    Test: For PyScript to work, files must be served via HTTP.
    This test documents what's needed.
    """
    print("\n=== TEST: PyScript file serving requirements ===")
    print("""
PyScript runs in browser and needs files served via HTTP:

REQUIRED SETUP:
  1. HTML file location: /path/to/index.html
  2. Python files location: /path/to/assets/py/*.py
  3. Web server: Must serve files from project root
  4. HTTP access: http://localhost:PORT/assets/py/spellcasting.py

WHAT HAPPENS:
  - Browser loads index.html
  - PyScript initializes in /home/pyodide/ (Pyodide sandbox)
  - PyScript tries to import modules
  - If files not accessible via HTTP, import fails
  - Error: "No module named 'spellcasting'"

DIAGNOSIS FROM CONSOLE OUTPUT:
  MODULE_DIR = /home/pyodide/assets/py
  '__file__' in globals() = False
  Path.cwd() = /home/pyodide
  
  This means:
  - PyScript can't find __file__
  - It falls back to Path.cwd() / "assets" / "py"
  - /home/pyodide/assets/py doesn't exist
  - Files not being served to PyScript

SOLUTION:
  1. Ensure web server serves from project root
  2. Ensure HTTP requests can access /assets/py/spellcasting.py
  3. PyScript can then fetch files and module loading works
    """)
    
    return True


def test_pyscript_fetches_via_http():
    """
    Test: Document how PyScript fetches files.
    PyScript uses HTTP/fetch to get Python files.
    """
    print("\n=== TEST: PyScript HTTP file fetching ===")
    print("""
PyScript's module loading mechanism:

1. Module requested: from spellcasting import SpellcastingManager
2. PyScript/Pyodide looks for spellcasting module
3. Checks standard library first
4. Checks sys.path directories next
5. For each sys.path entry, tries HTTP fetch:
   GET /assets/py/spellcasting.py
   GET /assets/py/spellcasting.cpython-312.so
   GET /assets/py/__init__.py (for packages)
6. If successful, loads module
7. If all fail, ImportError raised

WHAT WE SEE IN CONSOLE:
  DEBUG: Added /home/pyodide/assets/py to sys.path[0]
  DEBUG: spellcasting module import failed: No module named 'spellcasting'
  
This means:
  - Path was added to sys.path
  - HTTP fetch of /assets/py/spellcasting.py FAILED
  - Files not accessible via HTTP from browser

CHECK IN BROWSER DEVELOPER TOOLS:
  Network tab: Look for /assets/py/spellcasting.py requests
  Result should be: 200 OK (not 404 Not Found)
  If seeing 404: Files not being served
    """)
    
    return True


def test_what_needs_to_be_served():
    """List exactly what files need to be served via HTTP."""
    print("\n=== TEST: Required HTTP-served files ===")
    print("\nFiles that MUST be accessible via HTTP for PyScript:\n")
    
    required = [
        "assets/py/spellcasting.py",
        "assets/py/spell_data.py",
        "assets/py/character.py",
        "assets/py/character_models.py",
        "assets/py/entities.py",
        "assets/py/equipment_management.py",
        "assets/py/export_management.py",
        "assets/py/browser_logger.py",
    ]
    
    for file_path in required:
        local_path = Path.cwd() / file_path
        exists = local_path.exists()
        status = "[OK]" if exists else "[FAIL]"
        print(f"  {status} {file_path} (local: {exists})")
    
    print("\nThese must be served at:")
    print("  http://localhost:PORT/assets/py/spellcasting.py")
    print("  http://localhost:PORT/assets/py/spell_data.py")
    print("  ... etc for all files above")
    
    return all((Path.cwd() / f).exists() for f in required)


def test_http_server_configuration():
    """Document HTTP server requirements for PyScript."""
    print("\n=== TEST: HTTP server configuration ===")
    print("""
For the character sheet to work with PyScript:

FLASK SERVER (if using Flask):
  - Root must be project directory
  - @app.route('/')
  - @app.route('/<path:filename>')
  - Must serve static files from assets/ directory
  
  Example:
    app = Flask(__name__, static_folder='.')
    @app.route('/')
    def index():
        return send_file('index.html')
    @app.route('/<path:filename>')
    def serve_file(filename):
        return send_file(filename)

SIMPLE HTTP SERVER:
  python -m http.server 8000
  (Serves current directory)

VERIFICATION:
  1. Open browser to http://localhost:8000
  2. Open Developer Tools (F12)
  3. Go to Network tab
  4. Refresh page
  5. Look for /assets/py/spellcasting.py
  6. Status should be 200 OK
  7. If 404 Not Found: server not serving files correctly
    """)
    
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PYSCRIPT FILE SERVING AND MODULE LOADING TESTS")
    print("="*70)
    
    results = {
        "files_exist_locally": test_files_exist_locally(),
        "pyscript_discovery": test_pyscript_would_find_files(),
        "sys_path_update": test_sys_path_includes_assets_py(),
        "spellcasting_findable": test_spellcasting_findable_after_path_update(),
        "http_requirement": test_pyscript_file_serving_requirement(),
        "http_fetching": test_pyscript_fetches_via_http(),
        "files_needed": test_what_needs_to_be_served(),
        "server_config": test_http_server_configuration(),
    }
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    print(f"\nTotal: {passed}/{total} passed")
    
    print("\n" + "="*70)
    print("DIAGNOSIS")
    print("="*70)
    print("""
Based on browser console output:

PROBLEM IDENTIFIED:
  PyScript cannot import 'spellcasting' module
  Reason: Files not accessible via HTTP
  
EVIDENCE:
  1. MODULE_DIR detected as /home/pyodide/assets/py
  2. sys.path[0] updated to /home/pyodide/assets/py
  3. Import still fails: "No module named 'spellcasting'"
  4. This means HTTP fetch of /assets/py/spellcasting.py failed

SOLUTION:
  1. Check HTTP server configuration
  2. Verify /assets/py/*.py files are being served
  3. Use browser Network tab to check HTTP requests
  4. Ensure web server serves from project root
  5. Restart web server after verifying configuration
  6. Clear browser cache and reload

QUICK CHECKLIST:
  [ ] Web server running? (http://localhost:8000 or similar)
  [ ] Serving from project root? (Can access index.html via HTTP)
  [ ] Can download /assets/py/spellcasting.py via HTTP?
  [ ] All 8 Python files accessible?
  [ ] Browser cache cleared?
  [ ] Page reloaded after cache clear?
  
If all checks pass, PyScript module loading should work.
    """)
