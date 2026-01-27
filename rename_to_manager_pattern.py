"""
Script to rename files to consistent *_manager.py pattern and update all imports.

Renames:
- equipment_management.py → inventory_manager.py
- spellcasting.py → spellcasting_manager.py  
- event_listener.py → equipment_event_manager.py
"""

import os
import re
from pathlib import Path

# Define renames
RENAMES = {
    "equipment_management": "inventory_manager",
    "spellcasting": "spellcasting_manager",
    "event_listener": "equipment_event_manager",
}

def update_imports_in_file(filepath: Path):
    """Update import statements in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update each import
        for old_name, new_name in RENAMES.items():
            # Match: from inventory_manager import ...
            content = re.sub(
                rf'\bfrom {old_name} import\b',
                f'from {new_name} import',
                content
            )
            # Match: import inventory_manager
            content = re.sub(
                rf'\bimport {old_name}\b',
                f'import {new_name}',
                content
            )
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error updating {filepath}: {e}")
        return False

def rename_files(base_dir: Path):
    """Rename the actual Python files."""
    py_dir = base_dir / "static" / "assets" / "py"
    
    for old_name, new_name in RENAMES.items():
        old_path = py_dir / f"{old_name}.py"
        new_path = py_dir / f"{new_name}.py"
        
        if old_path.exists():
            os.rename(old_path, new_path)
            print(f"✓ Renamed: {old_name}.py → {new_name}.py")
        else:
            print(f"⚠ Not found: {old_path}")

def main():
    base_dir = Path(__file__).parent
    
    print("=" * 60)
    print("STEP 1: Updating imports in all Python files")
    print("=" * 60)
    
    # Find all Python files
    py_files = list(base_dir.rglob("*.py"))
    updated_count = 0
    
    for py_file in py_files:
        if update_imports_in_file(py_file):
            updated_count += 1
    
    print(f"\nUpdated {updated_count} files")
    
    print("\n" + "=" * 60)
    print("STEP 2: Renaming module files")
    print("=" * 60)
    
    rename_files(base_dir)
    
    print("\n" + "=" * 60)
    print("DONE! Restart the server to load renamed modules.")
    print("=" * 60)

if __name__ == "__main__":
    main()
