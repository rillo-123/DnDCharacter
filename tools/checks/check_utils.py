"""Shared utilities for check scripts.

Consolidates common boilerplate for argument parsing and JSON loading.
"""

from pathlib import Path
import argparse
import json
from typing import Optional, Dict, Any, Callable


def find_default_export(exports_dir: Path) -> Optional[Path]:
    """Find the most recent export JSON file in a directory.
    
    Args:
        exports_dir: Directory to search for export files
        
    Returns:
        Path to most recent export JSON file, or None if no files found
    """
    files = sorted(
        (p for p in exports_dir.glob("*.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def build_arg_parser(description: str, add_domain_args: bool = False) -> argparse.ArgumentParser:
    """Build argument parser with common arguments for check scripts.
    
    Args:
        description: Script description for help text
        add_domain_args: If True, add --domain and --level arguments
        
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to an export JSON. If omitted, uses newest in exports/."
    )
    parser.add_argument(
        "--exports-dir",
        type=Path,
        default=Path("exports"),
        help="Directory containing export JSON files."
    )
    if add_domain_args:
        parser.add_argument(
            "--domain",
            default="life",
            help="Domain name to evaluate (default: life)."
        )
        parser.add_argument(
            "--level",
            type=int,
            default=9,
            help="Character level to use for domain bonus calculation (default: 9)."
        )
    return parser


def resolve_export_path(args: argparse.Namespace, exports_dir_base: Optional[Path] = None) -> Optional[Path]:
    """Resolve the export file path from command-line arguments.
    
    Handles relative path resolution and finding default exports.
    
    Args:
        args: Parsed command-line arguments (must have --file and --exports-dir)
        exports_dir_base: Base directory for relative path resolution. 
                         If None, uses parent of calling script (2 levels up)
        
    Returns:
        Resolved Path to export JSON file, or None if not found
    """
    if exports_dir_base is None:
        exports_dir_base = Path(__file__).resolve().parents[2]
    
    exports_dir = args.exports_dir
    if not exports_dir.is_absolute():
        exports_dir = exports_dir_base / exports_dir
    
    if args.file:
        export_path = args.file
        if not export_path.is_absolute():
            export_path = exports_dir_base / export_path
    else:
        export_path = find_default_export(exports_dir)
        if export_path is None:
            print(f"No export JSON files found in {exports_dir}")
            return None
    
    return export_path


def load_export_json(export_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse an export JSON file.
    
    Args:
        export_path: Path to export JSON file
        
    Returns:
        Parsed JSON data, or None if load fails
    """
    try:
        return json.loads(export_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Failed to load export JSON: {export_path} ({exc})")
        return None


def run_check_main(
    check_func: Callable,
    add_domain_args: bool = False
) -> int:
    """Helper to run a check script's main logic with standard boilerplate.
    
    Handles argument parsing, export resolution, and JSON loading.
    The check_func receives the parsed data and args, and returns exit code.
    
    Args:
        check_func: Function(data: Dict, args: Namespace) -> int
        add_domain_args: If True, add --domain and --level arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import sys
    
    # Get the calling script's docstring
    frame = sys._getframe(1)
    docstring = frame.f_globals.get("__doc__", "Check script")
    
    # Build parser and parse arguments
    parser = build_arg_parser(docstring, add_domain_args=add_domain_args)
    args = parser.parse_args()
    
    # Resolve export path
    export_path = resolve_export_path(args)
    if export_path is None:
        return 1
    
    # Load JSON data
    data = load_export_json(export_path)
    if data is None:
        return 1
    
    # Run the check function with loaded data
    return check_func(data, args, export_path)
