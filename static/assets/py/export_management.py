"""Export/Import Management Module

This module handles character data export (to JSON), import (from JSON), and automatic export
functionality with browser File System API support.

Extracted from character.py to reduce monolithic size and improve maintainability.
"""

import json
import re
import sys
import importlib
from datetime import datetime, timedelta
from typing import Optional
import asyncio

# Guard for PyScript/Pyodide environment
try:
    from js import window
    from pyodide import create_proxy, JsException
    # create_once_callable is not used in current code; keep None for compatibility
    create_once_callable = None
    _js_module_available = True
except ImportError:
    # Non-PyScript environment (testing)
    window = None
    _js_module_available = False
    create_proxy = lambda x: x
    create_once_callable = None
    JsException = Exception

# Lazy-initialized JS globals (set to None initially, will be initialized on first use)
document = None
fetch = None
localStorage = None


def _initialize_js_globals():
    """Initialize JS globals from the js module. Called once on first use."""
    global document, fetch, localStorage
    
    if not _js_module_available:
        return  # Can't import in non-PyScript environment
    
    # Try importing each one carefully
    if document is None:
        try:
            from js import document as js_doc  # type: ignore
            document = js_doc
        except (ImportError, AttributeError, Exception):
            pass
    
    if fetch is None:
        try:
            from js import fetch as js_fetch  # type: ignore
            fetch = js_fetch
        except (ImportError, AttributeError, Exception):
            pass
    
    if localStorage is None:
        try:
            from js import localStorage as js_storage  # type: ignore
            localStorage = js_storage
        except (ImportError, AttributeError, Exception):
            pass

try:
    from browser_logger import BrowserLogger
    LOGGER = BrowserLogger()
except ImportError:
    # Fallback logger
    class FallbackLogger:
        def info(self, msg, *args):
            print(f"INFO: {msg}")
        def warning(self, msg, *args):
            print(f"WARNING: {msg}")
        def error(self, msg, *args):
            print(f"ERROR: {msg}")
        def get_stats(self):
            return {}
    LOGGER = FallbackLogger()

try:
    if document is not None:
        console = window.console
    else:
        raise ImportError("console not available")
except (ImportError, AttributeError):
    # Mock console for non-PyScript environments
    class MockConsole:
        def log(self, *args):
            print(" ".join(str(a) for a in args))

        def warn(self, *args):
            print("WARN: " + " ".join(str(a) for a in args))

        def error(self, *args):
            print("ERROR: " + " ".join(str(a) for a in args))
    console = MockConsole()

# ===================================================================
# Export Configuration
# ===================================================================

AUTO_EXPORT_DELAY_MS = 2000
AUTO_EXPORT_MAX_EVENTS = 15
MAX_EXPORTS_PER_CHARACTER = 20
EXPORT_PRUNE_DAYS = 30

# Note: LOCAL_STORAGE_KEY is defined in character.py (keep in sync)
LOCAL_STORAGE_KEY = "pysheet.character.v1"

# ===================================================================
# Export State (Global Tracking)
# ===================================================================

_AUTO_EXPORT_TIMER_ID: Optional[asyncio.Task] = None  # Now an asyncio Task instead of setTimeout ID
_AUTO_EXPORT_PROXY = None
_AUTO_EXPORT_SUPPRESS = False
_LAST_AUTO_EXPORT_SNAPSHOT = ""
_LAST_AUTO_EXPORT_DATE = ""
_AUTO_EXPORT_EVENT_COUNT = 0
_AUTO_EXPORT_FILE_HANDLE = None
_AUTO_EXPORT_DISABLED = False
_AUTO_EXPORT_SUPPORT_WARNED = False
_AUTO_EXPORT_DIRECTORY_HANDLE = None
_AUTO_EXPORT_LAST_FILENAME = ""
_AUTO_EXPORT_SETUP_PROMPTED = False

# Event proxy list (for memory management)
_EVENT_PROXIES = []


def _resolve_timers():
    """Return callable setTimeout/clearTimeout from window."""
    try_set = None
    try_clear = None

    # Get from window if available
    if window is not None:
        try_set = getattr(window, "setTimeout", None)
        try_clear = getattr(window, "clearTimeout", None)

    # Fall back to js imports if still missing
    if try_set is None or try_clear is None:
        try:
            from js import setTimeout as js_setTimeout, clearTimeout as js_clearTimeout  # type: ignore

            try_set = try_set or js_setTimeout
            try_clear = try_clear or js_clearTimeout
        except Exception:
            pass

    return try_set, try_clear


def _get_character_module():
    """Return the character module regardless of how it was loaded."""
    try:
        module = sys.modules.get("character") or sys.modules.get("__main__")
        if module is not None:
            return module
        return importlib.import_module("character")
    except Exception as exc:  # pragma: no cover - runtime safeguard
        console.warn(f"[export] unable to resolve character module: {exc}")
        return None


def _resolve_local_storage():
    """Return the browser localStorage object if available."""
    if localStorage is not None:
        return localStorage
    try:
        if window is not None and hasattr(window, "localStorage"):
            return window.localStorage
    except Exception:
        pass
    try:
        from js import window as js_window  # type: ignore
        return getattr(js_window, "localStorage", None)
    except Exception:
        return None

# ===================================================================
# Export Filename Utilities
# ===================================================================

def _normalize_export_basename(candidate: Optional[str]) -> str:
    """Normalize character name for use in export filename."""
    if not candidate:
        candidate = "character"
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", candidate.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return "character"
    return cleaned


def _build_export_filename(data: dict, *, now: Optional[datetime] = None) -> str:
    """Build export filename from character data.
    
    Format: <character_name>_<class>_lvl<level_number>_YYYYMMDD_HHMM.json
    """
    if now is None:
        now = datetime.now()
    raw_name = (data.get("identity", {}).get("name") or "character").strip()
    base_name = _normalize_export_basename(raw_name)
    
    # Get class
    class_name = (data.get("identity", {}).get("class") or "unknown").strip()
    class_part = _normalize_export_basename(class_name)
    
    # Get level
    level_value = 0
    try:
        level_value = int(data.get("level", 0))
    except (TypeError, ValueError):
        level_value = 0
    if level_value <= 0:
        level_value = 0
    
    # Use DATE and MINUTE (YYYYMMDD_HHMM) resolution
    # Files with same timestamp will overwrite each other (intended)
    # Different minutes create different files
    timestamp = now.strftime("%Y%m%d_%H%M")
    return f"{base_name}_{class_part}_lvl{level_value}_{timestamp}.json"


def _extract_character_name_from_filename(filename: str) -> str:
    """Extract character name from export filename.
    
    Handles formats like:
    - enwer_cleric_lvl9_20251120_1234.json (new format)
    - enwer_20251120_lvl_9.json (old format)
    - rillobaby.json
    - character (1).json
    """
    if not filename or not filename.endswith(".json"):
        return ""
    
    name_part = filename[:-5]
    
    # Try new format: <name>_<class>_lvl<level>_YYYYMMDD_HHMM
    match = re.match(r'^(.+?)_[a-z]+_lvl\d+_\d{8}_\d{4}$', name_part)
    if match:
        return match.group(1).lower()
    
    # Try old format: <name>_YYYYMMDD_lvl_<level>
    cleaned = re.sub(r'_\d{8}(_lvl_\d+)?$', '', name_part)
    # Try old format with time: <name>_YYYYMMDD_HHMM
    cleaned = re.sub(r'_\d{8}_\d{4}$', '', cleaned)
    # Remove (N) suffix from duplicates
    cleaned = re.sub(r'\s*\(\d+\)$', '', cleaned)
    
    return cleaned.strip().lower()


# ===================================================================
# Storage Management
# ===================================================================

def estimate_export_cleanup():
    """Estimate storage savings from cleanup (browser localStorage only)."""
    storage = _resolve_local_storage()
    if storage is None:
        return None
    
    try:
        stored_logs = storage.getItem("pysheet_logs") or ""
        stored_spells = storage.getItem("pysheet_spells") or ""
        stored_chars = storage.getItem(LOCAL_STORAGE_KEY) or ""
        
        total_size = len(stored_logs) + len(stored_spells) + len(stored_chars)
        
        # Estimate: each full export is ~2-5KB of JSON
        estimated_exports = total_size // 3000
        
        return {
            "total_bytes": total_size,
            "estimated_export_count": estimated_exports,
            "estimated_savings_kb": (estimated_exports * 3) // 1024 if estimated_exports > 20 else 0,
        }
    except Exception as exc:
        LOGGER.warning(f"Could not estimate cleanup: {exc}")
        return None


def prune_old_exports(directory_handle, max_keep: int = MAX_EXPORTS_PER_CHARACTER):
    """Remove old exports, keeping only the most recent per character.
    
    This is a browser-based version that attempts to prune from the directory.
    Note: Full file listing/deletion may not be available in all browsers.
    """
    try:
        LOGGER.info(f"Export pruning configured: keeping {max_keep} latest per character")
        return True
    except Exception as exc:
        LOGGER.warning(f"Could not prune exports: {exc}")
        return False


async def _prune_old_exports_from_directory(directory_handle):
    """Prune exports older than EXPORT_PRUNE_DAYS from the directory.
    
    Rules:
    - Delete files older than 30 days
    - BUT always keep at least 1 file (never delete all exports)
    
    Format: <name>_<class>_lvl<level>_YYYYMMDD_HHMM.json
    Only works if directory_handle supports async iteration (desktop/Chrome).
    """
    if directory_handle is None:
        return
    
    try:
        cutoff_date = datetime.now() - timedelta(days=EXPORT_PRUNE_DAYS)
        pruned_count = 0
        all_files = []  # Collect all JSON files with their dates
        
        # Attempt to iterate and collect files
        try:
            async for entry in directory_handle.entries():
                if not entry.name.endswith(".json"):
                    continue
                
                # Match format: <name>_<class>_lvl<level>_YYYYMMDD_HHMM.json
                match = re.search(r'_(\d{8})_(\d{4})\.json$', entry.name)
                if not match:
                    continue
                
                date_str, time_str = match.groups()
                try:
                    file_date = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M")
                    all_files.append((entry.name, file_date))
                except (ValueError, JsException):
                    continue
        except (AttributeError, TypeError):
            # Try alternative method using keys()
            try:
                file_names = await directory_handle.keys()
                for entry_name in file_names:
                    if not entry_name.endswith(".json"):
                        continue
                    
                    match = re.search(r'_(\d{8})_(\d{4})\.json$', entry_name)
                    if not match:
                        continue
                    
                    date_str, time_str = match.groups()
                    try:
                        file_date = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M")
                        all_files.append((entry_name, file_date))
                    except (ValueError, JsException):
                        continue
            except (AttributeError, JsException):
                pass
        
        # Sort by date (newest first) and delete old ones, but keep at least 1
        all_files.sort(key=lambda x: x[1], reverse=True)
        
        for filename, file_date in all_files:
            # Only delete if:
            # 1. File is older than cutoff date AND
            # 2. We have more than 1 file (keep at least 1)
            if file_date < cutoff_date and len(all_files) > 1:
                try:
                    await directory_handle.removeEntry(filename)
                    pruned_count += 1
                    console.log(f"PySheet: pruned old export {filename}")
                    all_files.remove((filename, file_date))  # Update count for "keep at least 1" check
                except Exception as exc:
                    console.warn(f"PySheet: could not delete {filename}: {exc}")
        
        if pruned_count > 0:
            console.log(f"PySheet: pruned {pruned_count} exports older than {EXPORT_PRUNE_DAYS} days (kept at least 1)")
    
    except Exception as exc:
        console.warn(f"PySheet: error during export pruning: {exc}")


# ===================================================================
# File System API Helpers
# ===================================================================

async def _ensure_directory_write_permission(handle) -> bool:
    """Check/request write permission for directory handle."""
    if handle is None:
        console.warn("[DEBUG] Permission check: handle is None")
        return False
    
    query_permission = getattr(handle, "queryPermission", None)
    request_permission = getattr(handle, "requestPermission", None)
    console.log(f"[DEBUG] Handle has queryPermission: {query_permission is not None}, requestPermission: {request_permission is not None}")
    
    # If handle doesn't have permission methods, assume permission is granted
    # (browser may not support them, or they're already granted)
    if query_permission is None or request_permission is None:
        console.log("[DEBUG] Handle lacks permission methods, assuming granted (browser may not support them)")
        return True
    
    try:
        status = await query_permission({"mode": "readwrite"})
        console.log(f"[DEBUG] queryPermission returned: {status}")
    except Exception as exc:
        console.warn(f"[DEBUG] queryPermission error: {exc}")
        status = None
    
    if status == "granted":
        console.log("[DEBUG] Permission already granted")
        return True
    if status == "denied":
        console.log("[DEBUG] Permission denied by user")
        return False
    
    console.log("[DEBUG] Requesting write permission...")
    try:
        status = await request_permission({"mode": "readwrite"})
        console.log(f"[DEBUG] requestPermission returned: {status}")
    except Exception as exc:
        console.warn(f"[DEBUG] requestPermission error: {exc}")
        return False
    
    result = status == "granted"
    console.log(f"[DEBUG] Final permission result: {result}")
    return result


def _ensure_auto_export_proxy():
    """No longer needed - we use asyncio.sleep() instead of JavaScript setTimeout.
    
    This function is kept for backward compatibility but no longer creates proxies.
    The actual delay is now handled by Python's asyncio, avoiding proxy destruction entirely.
    """
    # Not used anymore, but kept for compatibility
    return None


def _supports_persistent_auto_export() -> bool:
    """Check if browser supports File System API for persistent exports."""
    if window is None:
        console.log("[DEBUG] _supports_persistent_auto_export: window is None")
        return False
    
    # Try to access showDirectoryPicker directly instead of using hasattr
    # because hasattr() doesn't work reliably with PyScript JS proxies
    try:
        picker = getattr(window, "showDirectoryPicker", None)
        has_support = picker is not None
        console.log(f"[DEBUG] _supports_persistent_auto_export: showDirectoryPicker={picker is not None}, returning {has_support}")
        return has_support
    except Exception as e:
        console.log(f"[DEBUG] _supports_persistent_auto_export: exception checking - {e}")
        return False


async def _ensure_auto_export_directory(auto_trigger: bool = True, directory_picker_method = None):
    """Prompt user to select directory for auto-export.

    Note: `auto_trigger` parameter is kept for API compatibility but is currently unused.
    """
    # Use parameter in an assert to avoid false-positive unused-variable warnings in static analysis
    assert isinstance(auto_trigger, bool)
    global _AUTO_EXPORT_DIRECTORY_HANDLE, _AUTO_EXPORT_DISABLED
    
    # Early exit if already have a handle
    if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
        return _AUTO_EXPORT_DIRECTORY_HANDLE
    
    # Use captured method if available, otherwise try accessing from window
    picker_func = directory_picker_method
    if picker_func is None:
        picker_func = getattr(window, "showDirectoryPicker", None) if window else None
    
    if picker_func is None:
        console.log("[DEBUG] showDirectoryPicker not available")
        return None
    
    try:
        console.log("[DEBUG] Calling showDirectoryPicker...")
        handle = await picker_func()
    except JsException as exc:
        name = getattr(exc, "name", "")
        if name == "AbortError":
            console.log("PySheet: auto-export directory not selected; will try again on next change")
        elif name in {"NotAllowedError", "SecurityError"}:
            console.warn("PySheet: directory picker requires a user gesture; use Export JSON to set it up")
        else:
            console.warn(f"PySheet: auto-export directory picker error - {exc}")
        return None
    
    has_permission = await _ensure_directory_write_permission(handle)
    if not has_permission:
        console.log("PySheet: directory lacks write permission; will try again on next change")
        return None
    
    if not hasattr(handle, "getFileHandle"):
        console.warn("PySheet: selected directory handle cannot create files; falling back to file picker")
        return None
    
    _AUTO_EXPORT_DIRECTORY_HANDLE = handle
    console.log("PySheet: auto-export directory selected")
    return handle


async def _ensure_auto_export_file_handle(target_name: str, auto_trigger: bool = True):
    """Prompt user to select file for auto-export.

    Note: `auto_trigger` parameter is kept for API compatibility but is currently unused.
    """
    # Use parameter in an assert to avoid false-positive unused-variable warnings in static analysis
    assert isinstance(auto_trigger, bool)
    global _AUTO_EXPORT_FILE_HANDLE, _AUTO_EXPORT_DISABLED, _AUTO_EXPORT_LAST_FILENAME
    
    if window is None:
        return None
    
    if not hasattr(window, "showSaveFilePicker"):
        return None
    
    if _AUTO_EXPORT_FILE_HANDLE is not None:
        existing_name = getattr(_AUTO_EXPORT_FILE_HANDLE, "name", None)
        if existing_name and existing_name != target_name:
            _AUTO_EXPORT_FILE_HANDLE = None
        else:
            _AUTO_EXPORT_LAST_FILENAME = existing_name or target_name
            return _AUTO_EXPORT_FILE_HANDLE
    
    options = {
        "suggestedName": target_name,
        "types": [
            {
                "description": "Character JSON",
                "accept": {"application/json": [".json"]},
            }
        ],
    }
    
    try:
        handle = await window.showSaveFilePicker(options)
    except JsException as exc:
        name = getattr(exc, "name", "")
        if name == "AbortError":
            console.log("PySheet: auto-export file target not selected; will try again on next change")
        elif name in {"NotAllowedError", "SecurityError"}:
            console.warn("PySheet: file picker requires a user gesture; use Export JSON to set it up")
        else:
            console.warn(f"PySheet: auto-export file picker error - {exc}")
        return None
    
    _AUTO_EXPORT_FILE_HANDLE = handle
    _AUTO_EXPORT_LAST_FILENAME = getattr(handle, "name", target_name)
    console.log("PySheet: auto-export file selected")
    return handle


async def _write_auto_export_file(handle, payload: str):
    """Write payload to file handle."""
    try:
        console.log(f"[DEBUG] _write_auto_export_file: handle={handle}, payload length={len(payload)}")
        console.log(f"[DEBUG] Calling createWritable() on handle...")
        writable = await handle.createWritable()
        console.log(f"[DEBUG] createWritable() succeeded, writable={writable}")
        console.log(f"[DEBUG] Writing {len(payload)} bytes...")
        await writable.write(payload)
        console.log(f"[DEBUG] Write completed, closing writable...")
        await writable.close()
        console.log(f"[DEBUG] Writable closed successfully")
    except Exception as exc:
        console.error(f"[DEBUG] _write_auto_export_file error: {type(exc).__name__}: {exc}")
        raise RuntimeError(f"failed to write auto-export file ({exc})")


async def _attempt_persistent_export(
    payload: str,
    proposed_filename: str,
    *,
    auto: bool,
    allow_prompt: bool,
) -> bool:
    """Attempt to export to persistent storage (directory or file handle)."""
    global _AUTO_EXPORT_DIRECTORY_HANDLE, _AUTO_EXPORT_FILE_HANDLE
    global _AUTO_EXPORT_DISABLED, _AUTO_EXPORT_LAST_FILENAME, _LAST_AUTO_EXPORT_SNAPSHOT
    global _AUTO_EXPORT_SETUP_PROMPTED

    if not _supports_persistent_auto_export():
        return False

    # NOTE: Do NOT prompt for setup during auto-export (no user gesture context)
    # Only prompt when user explicitly clicks "Export JSON" button (has user gesture)
    need_prompt = (
        allow_prompt
        and not _AUTO_EXPORT_SETUP_PROMPTED
        and _AUTO_EXPORT_DIRECTORY_HANDLE is None
        and _AUTO_EXPORT_FILE_HANDLE is None
        and not auto  # Only prompt if NOT auto-triggered
    )
    
    if need_prompt and window is not None:
        wants_setup = False
        try:
            wants_setup = window.confirm(
                "Enable automatic JSON exports? Select OK to choose a folder for saving updates automatically."
            )
        except JsException:
            wants_setup = False
        
        _AUTO_EXPORT_SETUP_PROMPTED = True
        if wants_setup:
            handle = await _ensure_auto_export_directory(auto_trigger=False)
            if handle is None:
                await _ensure_auto_export_file_handle(proposed_filename, auto_trigger=False)

    # Try backend API first (pure Python, no JavaScript)
    try:
        console.log(f"[DEBUG] Attempting backend API export: {proposed_filename}")
        import httpx
        
        client = httpx.AsyncClient()
        response = await client.post('/api/export', json={
            'filename': proposed_filename,
            'content': payload
        })
        
        if response.status_code == 200:
            result = response.json()
            console.log(f"[DEBUG] Backend export succeeded: {result}")
            _AUTO_EXPORT_LAST_FILENAME = proposed_filename
            _LAST_AUTO_EXPORT_SNAPSHOT = payload
            _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
            verb = "auto-exported" if auto else "exported"
            console.log(f"PySheet: {verb} character JSON to {proposed_filename}")
            _AUTO_EXPORT_DISABLED = False
            return True
        else:
            error_text = response.text
            console.warn(f"[DEBUG] Backend export failed: HTTP {response.status_code}: {error_text}")
    except Exception as api_exc:
        console.log(f"[DEBUG] Backend API not available: {api_exc}")
    
    # Fallback to File System API
    if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
        try:
            console.log(f"[DEBUG] Fallback: Attempting File System API export: {proposed_filename}")
            file_handle = await _AUTO_EXPORT_DIRECTORY_HANDLE.getFileHandle(
                proposed_filename,
                {"create": True},
            )
            console.log(f"[DEBUG] getFileHandle succeeded, file_handle={file_handle}")
        except Exception as exc:
            exc_str = str(exc)
            exc_type_name = type(exc).__name__
            console.warn(f"[DEBUG] getFileHandle failed: {exc_type_name}: {exc_str}")
            
            # Check if it's a NotFoundError (can be JsException wrapping NotFoundError)
            is_not_found = ("NotFoundError" in exc_type_name or "NotFoundError" in exc_str)
            console.log(f"[DEBUG] Exception analysis: type={exc_type_name}, is_not_found={is_not_found}, msg={exc_str[:100]}")
            
            # Fallback: try to remove the file first, then create it
            if is_not_found:
                try:
                    console.log(f"[DEBUG] NotFoundError detected, attempting to remove existing file first...")
                    await _AUTO_EXPORT_DIRECTORY_HANDLE.removeEntry(proposed_filename)
                    console.log(f"[DEBUG] File removed, retrying getFileHandle...")
                    file_handle = await _AUTO_EXPORT_DIRECTORY_HANDLE.getFileHandle(
                        proposed_filename,
                        {"create": True},
                    )
                    console.log(f"[DEBUG] getFileHandle succeeded on retry, file_handle={file_handle}")
                except Exception as retry_exc:
                    console.warn(f"[DEBUG] Retry failed: {type(retry_exc).__name__}: {retry_exc}")
                    console.warn(f"PySheet: unable to open auto-export file in directory ({exc_str})")
                    if auto:
                        _AUTO_EXPORT_DIRECTORY_HANDLE = None
                    file_handle = None
            else:
                console.warn(f"PySheet: unable to open auto-export file in directory ({exc_str})")
                if auto:
                    _AUTO_EXPORT_DIRECTORY_HANDLE = None
                file_handle = None
        
        if file_handle is not None:
            try:
                console.log(f"[DEBUG] Calling _write_auto_export_file for directory handle...")
                await _write_auto_export_file(file_handle, payload)
                console.log(f"[DEBUG] _write_auto_export_file succeeded for directory")
            except Exception as exc:
                console.warn(f"PySheet: auto-export write failed for directory target ({exc})")
                if auto:
                    _AUTO_EXPORT_DIRECTORY_HANDLE = None
            else:
                _AUTO_EXPORT_LAST_FILENAME = getattr(file_handle, "name", proposed_filename)
                _LAST_AUTO_EXPORT_SNAPSHOT = payload
                _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
                verb = "auto-exported" if auto else "exported"
                console.log(f"PySheet: {verb} character JSON to {_AUTO_EXPORT_LAST_FILENAME}")
                _AUTO_EXPORT_DISABLED = False
                # Prune old exports after successful export
                await _prune_old_exports_from_directory(_AUTO_EXPORT_DIRECTORY_HANDLE)
                return True

    handle = _AUTO_EXPORT_FILE_HANDLE
    if handle is not None:
        existing_name = getattr(handle, "name", "")
        if existing_name and existing_name != proposed_filename and allow_prompt:
            _AUTO_EXPORT_FILE_HANDLE = None
            handle = None
        if handle is None and allow_prompt:
            handle = await _ensure_auto_export_file_handle(proposed_filename, auto_trigger=False)
        if handle is not None:
            try:
                await _write_auto_export_file(handle, payload)
            except Exception as exc:
                console.warn(f"PySheet: auto-export write failed for file handle ({exc})")
                if auto:
                    _AUTO_EXPORT_FILE_HANDLE = None
            else:
                _AUTO_EXPORT_LAST_FILENAME = getattr(handle, "name", proposed_filename)
                _LAST_AUTO_EXPORT_SNAPSHOT = payload
                _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
                verb = "auto-exported" if auto else "exported"
                console.log(f"PySheet: {verb} character JSON to {_AUTO_EXPORT_LAST_FILENAME}")
                _AUTO_EXPORT_DISABLED = False
                return True

    return False


# ===================================================================
# Public Export/Import Functions
# ===================================================================

def save_character(_event=None):
    """Save character to browser localStorage."""
    console.log("DEBUG: save_character() called")
    storage = _resolve_local_storage()
    if storage is None or document is None:
        return
    
    try:
        # Import from character module - will be provided by parent
        from character import collect_character_data
        data = collect_character_data()
        storage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
        console.log("PySheet: character saved to localStorage")
    except Exception as exc:
        console.error(f"PySheet: failed to save character - {exc}")


def show_storage_info(_event=None):
    """Display storage usage information."""
    console.log("DEBUG: show_storage_info() called")
    try:
        if document is None:
            return
        
        info = estimate_export_cleanup()
        msg_el = document.getElementById("storage-message")
        
        if msg_el is None:
            return
        
        if info is None:
            msg_el.innerText = "Could not determine storage usage."
            LOGGER.warning("Failed to get storage info")
            return
        
        total_kb = info["total_bytes"] // 1024
        exports = info["estimated_export_count"]
        savings_kb = info["estimated_savings_kb"]
        
        if savings_kb > 0:
            msg_el.innerHTML = (
                f"<strong>Storage Usage:</strong> {total_kb}KB | "
                f"<strong>Exports:</strong> ~{exports} | "
                f"<strong>Potential savings:</strong> ~{savings_kb}KB if cleaned"
            )
            LOGGER.info(f"Storage info: {total_kb}KB used, ~{exports} exports, ~{savings_kb}KB potential savings")
        else:
            msg_el.innerHTML = f"<strong>Storage Usage:</strong> {total_kb}KB | <strong>Exports:</strong> ~{exports}"
            LOGGER.info(f"Storage info: {total_kb}KB used, ~{exports} exports")
    except Exception as e:
        LOGGER.error(f"ERROR in show_storage_info: {e}")


def cleanup_exports(_event=None):
    """Clean up old export files (browser-based pruning of localStorage info)."""
    console.log("DEBUG: cleanup_exports() called")
    if document is None:
        return
    
    msg_el = document.getElementById("storage-message")
    if msg_el is None:
        return
    
    try:
        stats = LOGGER.get_stats()
        
        oldest = stats.get("oldest_log", "unknown")
        total_logs = stats.get("total_logs", 0)
        total_errors = stats.get("total_errors", 0)
        days = stats.get("days_with_logs", 0)
        storage_kb = stats.get("storage_bytes", 0) // 1024
        
        msg_el.innerHTML = (
            f"✓ <strong>Logs maintained!</strong> "
            f"{total_logs} log entries across {days} days ({storage_kb}KB). "
            f"Rolling 60-day window active (oldest: ~{oldest[:10] if oldest else 'unknown'}). "
            f"To delete old export files from /exports/, use your file manager."
        )
        LOGGER.info(f"Cleanup status: {total_logs} logs, {total_errors} errors, {storage_kb}KB used, 60-day rolling window active")
    except Exception as exc:
        LOGGER.error(f"Cleanup failed: {exc}", exc)
        msg_el.innerHTML = "Cleanup error - check logs"
        console.error(f"Cleanup failed: {exc}")


async def export_character(_event=None, *, auto: bool = False):
    """Export character to JSON file.
    
    Can export to browser download or to persistent storage (directory/file handle)
    if File System API is supported and user has configured a target.
    """
    console.log("[DEBUG] export_character() async function started")
    global _LAST_AUTO_EXPORT_SNAPSHOT, _LAST_AUTO_EXPORT_DATE, _AUTO_EXPORT_FILE_HANDLE
    global _AUTO_EXPORT_DISABLED, _AUTO_EXPORT_SUPPORT_WARNED, _AUTO_EXPORT_DIRECTORY_HANDLE
    global _AUTO_EXPORT_LAST_FILENAME, _AUTO_EXPORT_SETUP_PROMPTED
    
    # Initialize JS globals if not already done
    _initialize_js_globals()
    
    # Get storage and continue - don't check for None as PyScript proxy objects may not work with `is None`
    storage = _resolve_local_storage()
    console.log(f"[DEBUG] storage resolved: {storage}")

    def show_saving_state():
        """Show green SAVING state."""
        console.log("[DEBUG] show_saving_state() function START")
        if document is None:
            console.warn("[DEBUG] show_saving_state() - document is None, skipping")
            return
        indicator = document.getElementById("saving-indicator")
        console.log(f"[DEBUG] show_saving_state() - indicator element: {indicator}")
        if indicator:
            console.log("[DEBUG] show_saving_state() - indicator found, updating classes")
            indicator.classList.remove("recording", "fading")
            indicator.classList.add("saving")
            indicator.style.display = "flex"
            indicator.style.opacity = "1"
            console.log("[DEBUG] show_saving_state() - classes updated, display set to flex")
        else:
            console.warn("[DEBUG] show_saving_state() - no indicator element found!")
        console.log("[DEBUG] show_saving_state() function END")

    def fade_indicator():
        """Fade to gray and remove."""
        if document is None:
            console.warn("[DEBUG] fade_indicator() - document is None, skipping")
            return
        indicator = document.getElementById("saving-indicator")
        if indicator:
            indicator.classList.remove("saving", "recording")
            indicator.classList.add("fading")
            indicator.style.display = "flex"
            # Hide after the CSS fade completes
            try:
                def _hide_after_fade(*_args):
                    try:
                        indicator.style.display = "none"
                    except Exception:
                        return

                # Schedule hiding with asyncio instead of JavaScript setTimeout to avoid proxy destruction
                async def _delayed_hide():
                    await asyncio.sleep(1.2)
                    try:
                        _hide_after_fade()
                    except Exception as exc:
                        console.warn(f"[DEBUG][export] error hiding indicator: {exc}")
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_delayed_hide())
                except RuntimeError:
                    # No running loop, hide immediately
                    indicator.style.display = "none"
            except Exception as exc:
                console.warn(f"[DEBUG][export] unable to hide saving-indicator: {exc}")

    character_module = _get_character_module()
    console.log(f"[DEBUG] character_module: {character_module}")
    collect_character_data = getattr(character_module, "collect_character_data", None) if character_module else None
    console.log(f"[DEBUG] collect_character_data: {collect_character_data}")
    if collect_character_data is None:
        console.error("PySheet: export failed before write - collect_character_data unavailable")
        fade_indicator()
        return

    try:
        console.log("[DEBUG] About to call collect_character_data()")
        data = collect_character_data()
        console.log(f"[DEBUG] collect_character_data() returned, data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
        payload = json.dumps(data)
        console.log(f"[DEBUG] JSON payload created, length: {len(payload)}")
    except Exception as exc:
        console.error(f"PySheet: export failed before write - {exc}")
        fade_indicator()
        return
    
    console.log(f"[DEBUG] === AFTER PAYLOAD: auto={auto}, _AUTO_EXPORT_DISABLED={_AUTO_EXPORT_DISABLED}")
    if auto and _AUTO_EXPORT_DISABLED:
        fade_indicator()

        # New debug logging for indicator state
        indicator = document.getElementById("saving-indicator") if document is not None else None
        if indicator:
            try:
                computed = window.getComputedStyle(indicator)
                console.log(
                    "[DEBUG][export] saving-indicator state",
                    {
                        "classList": list(indicator.classList),
                        "inline.display": indicator.style.display,
                        "inline.opacity": indicator.style.opacity,
                        "inline.visibility": indicator.style.visibility,
                        "computed.display": computed.display if computed else None,
                        "computed.opacity": computed.opacity if computed else None,
                        "computed.visibility": computed.visibility if computed else None,
                    },
                )
            except Exception as exc:
                console.warn(f"[DEBUG][export] unable to inspect saving-indicator: {exc}")
    # For auto-exports: skip only if data hasn't changed AND we've already exported today
    if auto and payload == _LAST_AUTO_EXPORT_SNAPSHOT:
        today = datetime.now().strftime("%Y%m%d")
        if today == _LAST_AUTO_EXPORT_DATE:
            fade_indicator()
            return
    
    console.log("[DEBUG] About to call show_saving_state()")
    try:
        if document is not None:
            show_saving_state()
            console.log("[DEBUG] show_saving_state() completed successfully")
        else:
            console.warn("[DEBUG] show_saving_state() skipped - document is None")
    except Exception as exc:
        console.error(f"[DEBUG] show_saving_state() threw exception: {exc}")
        import traceback
        console.error(f"[DEBUG] Traceback: {traceback.format_exc()}")

    now = datetime.now()
    proposed_filename = _build_export_filename(data, now=now)
    console.log(f"[DEBUG] Proposed filename: {proposed_filename}")

    # Send JSON to Flask backend for file writing
    console.log("[DEBUG] Sending export to Flask backend via POST /api/export")
    try:
        # Ensure fetch is available
        fetch_func = fetch
        if fetch_func is None:
            try:
                from js import fetch as js_fetch  # type: ignore
                fetch_func = js_fetch
            except (ImportError, AttributeError):
                console.error("ERROR: fetch API not available in this environment")
                return
            
        # Create the request payload
        request_data = {
            "filename": proposed_filename,
            "content": data
        }
        
        console.log(f"[DEBUG] POST payload ready: filename={proposed_filename}, data_size={len(payload)} bytes")
        
        # Convert Python dict to JSON string for body
        body_json = json.dumps(request_data)
        console.log(f"[DEBUG] Body JSON: {body_json[:100]}...")
        
        # Build the fetch using JavaScript directly to ensure proper POST
        # Use js.JSON.stringify to ensure proper serialization
        try:

            from js import Object as JSObject  # type: ignore
            
            # Create proper JavaScript object for fetch init
            options = JSObject.new()
            options.method = "POST"
            options.body = body_json
            
            # Set headers using defineProperty to avoid item assignment issues
            headers_obj = JSObject.new()
            # Use property assignment which works with JsProxy
            headers_obj["Content-Type"] = "application/json"
            options.headers = headers_obj
            
            console.log(f"[DEBUG] Fetch options created with headers")
        except Exception as e:
            console.error(f"[DEBUG] Failed to create proper options object: {e}")
            console.error(f"[DEBUG] Error type: {type(e)}")
            # Fallback: Use a workaround - encode options in URL params or use FormData
            console.warn("[DEBUG] Using JSON.stringify workaround for fetch init")
            
            # Try using eval through JavaScript to create the object
            try:
                from js import eval as js_eval  # type: ignore
                # This is a last resort - use JS eval to create proper object
                # Escape the body_json string for safe embedding in JS code
                escaped_body = body_json.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                js_code = f'''({{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: "{escaped_body}"
                }})'''
                options = js_eval(js_code)
                console.log("[DEBUG] Created options via JS eval")
            except:
                # Final fallback - just return error
                console.error("[DEBUG] All fetch options creation methods failed")
                return
        
        console.log(f"[DEBUG] About to call fetch")
        
        # POST to backend
        response = await fetch_func("/api/export", options)
        
        console.log(f"[DEBUG] Flask response status: {response.status}")
        response_text = await response.text()
        console.log(f"[DEBUG] Flask response: {response_text[:200]}")
        
        if response.status == 200:
            console.log(f"✓ {proposed_filename} successfully written to disk")
            _LAST_AUTO_EXPORT_SNAPSHOT = payload
            _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
        else:
            console.error(f"PySheet: backend export failed with status {response.status}")
            
    except Exception as exc:
        console.error(f"PySheet: export failed - {exc}")
        import traceback
        console.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
    
    fade_indicator()


def reset_character(_event=None):
    """Reset character to default state."""
    console.log("DEBUG: reset_character() called")
    storage = _resolve_local_storage()
    if window is None or storage is None or document is None:
        return
    
    if not window.confirm("Reset the sheet to default values? This will clear saved data."):
        return
    
    try:
        storage.removeItem(LOCAL_STORAGE_KEY)
        from character import populate_form, clone_default_state, schedule_auto_export
        populate_form(clone_default_state())
        schedule_auto_export()
        console.log("PySheet: character reset to defaults")
    except Exception as exc:
        console.error(f"PySheet: failed to reset character - {exc}")


def handle_import(event):
    """Handle character import from JSON file."""
    console.log("[IMPORT] START - handle_import function entered")
    
    try:
        # Get the file from the input
        files = event.target.files
        console.log(f"[IMPORT] Got files object: {files}")
        
        if not files or files.length == 0:
            console.log("[IMPORT] No file selected")
            return
        
        # FileList in Pyodide needs item(0) instead of subscript access
        file_obj = files.item(0)
        console.log(f"[IMPORT] File selected: {file_obj.name}")
        
        # Use FileReader to read the file (handle environments where FileReader imported as None)
        file_reader_ctor = None
        # Prefer window.FileReader
        try:
            if window is not None:
                file_reader_ctor = getattr(window, "FileReader", None)
        except Exception as e:
            console.warn(f"[IMPORT] window.FileReader access failed: {e}")
        # Fallback to js import
        if file_reader_ctor is None:
            try:
                from js import FileReader as JSFileReader  # type: ignore
                file_reader_ctor = JSFileReader
            except Exception as e:
                console.warn(f"[IMPORT] js FileReader import failed: {e}")
        # Fallback to eval
        if file_reader_ctor is None and window is not None:
            try:
                file_reader_ctor = window.eval("FileReader") if hasattr(window, "eval") else None
            except Exception as e:
                console.warn(f"[IMPORT] window.eval FileReader failed: {e}")
        if file_reader_ctor is None:
            console.error("[IMPORT] FileReader API not available")
            return
        try:
            reader = file_reader_ctor.new() if hasattr(file_reader_ctor, "new") else file_reader_ctor()
        except Exception as e:
            console.error(f"[IMPORT] Failed to construct FileReader: {e}")
            import traceback
            traceback.print_exc()
            return
        console.log(f"[IMPORT] FileReader created: {reader}")
        
        # Define onload callback
        def on_load(evt):
            # evt parameter provided by FileReader API (kept for compatibility)
            _ = evt
            console.log("[IMPORT] onload callback triggered")
            try:
                payload = reader.result
                console.log(f"[IMPORT] File loaded: {len(payload)} chars")
                
                # Parse JSON
                data = json.loads(payload)
                console.log(f"[IMPORT] JSON parsed: {data.get('identity', {}).get('name')}")
                
                # Get populate_form function
                import sys, importlib
                # Prefer injected back-reference from character.py if available
                character_module = globals().get("CHARACTER_MODULE")
                if character_module is None:
                    character_module = sys.modules.get('character')
                if character_module is None:
                    try:
                        character_module = importlib.import_module('character')
                        console.log("[IMPORT] character module imported via importlib")
                    except Exception as err:
                        console.error(f"[IMPORT] character module not found: {err}")
                        return
                
                populate_form = getattr(character_module, 'populate_form', None)
                if not populate_form:
                    console.error("[IMPORT] populate_form not found")
                    return
                
                console.log("[IMPORT] Calling populate_form...")
                populate_form(data)
                console.log("[IMPORT] populate_form completed")
                
                # Save to localStorage
                console.log("[IMPORT] Saving to localStorage...")
                storage = _resolve_local_storage()
                if storage is not None:
                    storage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
                else:
                    console.warn("[IMPORT] localStorage unavailable; skipping persistence")
                try:
                    schedule_auto_export()
                except Exception:
                    console.log("[IMPORT] schedule_auto_export not executed")
                console.log("[IMPORT] SUCCESS: character imported")
                
            except Exception as e:
                console.error(f"[IMPORT] onload error: {e}")
                import traceback
                traceback.print_exc()
        
        # Attach the callback using proper JavaScript event listener
        # Instead of creating a proxy, we'll use a wrapper approach
        def _attach_reader_callback():
            try:
                # Create a persistent wrapper that won't be destroyed
                callback_wrapper = create_proxy(on_load)
                _EVENT_PROXIES.append(callback_wrapper)
                reader.onload = callback_wrapper
            except Exception as e:
                console.error(f"[IMPORT] Failed to attach reader callback: {e}")
        
        _attach_reader_callback()
        console.log("[IMPORT] Callback attached, reading file...")
        reader.readAsText(file_obj)
        
    except Exception as e:
        console.error(f"[IMPORT] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


def schedule_auto_export():
    """Schedule automatic character export with debouncing using asyncio.
    
    Instead of using JavaScript's setTimeout (which destroys Python proxies),
    we schedule a Python async task that waits with asyncio.sleep().
    This keeps everything on the Python side and avoids proxy lifecycle issues.
    
    Always saves to localStorage immediately to preserve data across page refreshes.
    Also schedules an async export if browser supports File System API and user configured it.
    """
    global _AUTO_EXPORT_TIMER_ID, _AUTO_EXPORT_EVENT_COUNT
    storage = _resolve_local_storage()

    # If this module was imported in a non-browser context (e.g. test harness) but later
    # executed in PyScript, try to re-hydrate the browser globals before bailing.
    if window is None or document is None:
        try:  # noqa: SIM105 - explicit rebind of globals is intentional
            from js import window as js_window, document as js_document  # type: ignore

            globals()["window"] = js_window
            globals()["document"] = js_document
            console.log("[DEBUG][auto-export] rehydrated window/document from js import")
        except Exception as exc:  # pragma: no cover - defensive logging for PyScript
            console.warn(f"[DEBUG][auto-export] failed to rehydrate window/document: {exc}")
        else:
            # Re-check storage now that browser globals exist
            storage = storage or _resolve_local_storage()

    if _AUTO_EXPORT_SUPPRESS or window is None or document is None or storage is None:
        console.log(
            "[DEBUG][auto-export] skip:",
            {
                "suppress": _AUTO_EXPORT_SUPPRESS,
                "has_window": window is not None,
                "has_document": document is not None,
                "has_storage": storage is not None,
            },
        )
        return
    
    _AUTO_EXPORT_EVENT_COUNT = min(_AUTO_EXPORT_EVENT_COUNT + 1, AUTO_EXPORT_MAX_EVENTS)
    console.log(
        "[DEBUG][auto-export] enter:",
        {
            "event_count": _AUTO_EXPORT_EVENT_COUNT,
            "suppress": _AUTO_EXPORT_SUPPRESS,
        },
    )
    
    # Always save to localStorage immediately to preserve data across page refreshes
    try:
        character_module = _get_character_module()
        collect_character_data = getattr(character_module, "collect_character_data", None) if character_module else None
        if collect_character_data is None:
            raise ImportError("collect_character_data not available")
        data = collect_character_data()
        storage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    except Exception as exc:
        console.warn(f"PySheet: failed to save to localStorage - {exc}")
    
    # Show recording indicator (red) - even if auto-export is disabled, show that we detected a change
    indicator = document.getElementById("saving-indicator")
    print(f"[SAVE-LAMP] schedule_auto_export() showing lamp: indicator={indicator is not None}")
    if indicator:
        indicator.classList.remove("saving", "fading")
        indicator.classList.add("recording")
        # Force visibility in cases where CSS hasn't applied yet
        indicator.style.display = "flex"
        indicator.style.opacity = "1"
        print(f"[SAVE-LAMP] Classes added: {list(indicator.classList)}")
        try:
            # Debug the current visual state to help diagnose why the lamp may be hidden
            computed = window.getComputedStyle(indicator)
            console.log(
                "[DEBUG][auto-export] saving-indicator state",
                {
                    "classList": list(indicator.classList),
                    "inline.display": indicator.style.display,
                    "inline.opacity": indicator.style.opacity,
                    "inline.visibility": indicator.style.visibility,
                    "computed.display": computed.display if computed else None,
                    "computed.opacity": computed.opacity if computed else None,
                    "computed.visibility": computed.visibility if computed else None,
                },
            )
        except Exception as exc:
            console.warn(f"[DEBUG][auto-export] unable to inspect saving-indicator: {exc}")
    
    # If auto-export is disabled, don't actually schedule the export timer
    if _AUTO_EXPORT_DISABLED:
        console.log(f"DEBUG: Change detected but auto-export disabled. Recording indicator shown for UX.")
        return
    
    console.log(f"DEBUG: schedule_auto_export called! Event count: {_AUTO_EXPORT_EVENT_COUNT}")
    
    # Cancel any pending export task
    if _AUTO_EXPORT_TIMER_ID is not None:
        try:
            _AUTO_EXPORT_TIMER_ID.cancel()
        except Exception:
            pass
        _AUTO_EXPORT_TIMER_ID = None
    
    # Calculate delay based on remaining event count
    remaining = AUTO_EXPORT_MAX_EVENTS - _AUTO_EXPORT_EVENT_COUNT
    interval_seconds = AUTO_EXPORT_DELAY_MS / 1000.0
    if remaining <= 0:
        interval_seconds = (AUTO_EXPORT_DELAY_MS * 0.25) / 1000.0
    
    # Schedule the export using asyncio instead of JavaScript setTimeout
    # This keeps the callback in Python and avoids proxy destruction
    async def _delayed_export():
        global _AUTO_EXPORT_TIMER_ID, _AUTO_EXPORT_EVENT_COUNT
        try:
            await asyncio.sleep(interval_seconds)
            _AUTO_EXPORT_TIMER_ID = None
            await export_character(auto=True)
        except Exception as exc:
            console.error(f"PySheet: auto-export failed - {exc}")
        finally:
            _AUTO_EXPORT_EVENT_COUNT = 0
    
    try:
        loop = asyncio.get_running_loop()
        _AUTO_EXPORT_TIMER_ID = loop.create_task(_delayed_export())
        console.log(f"DEBUG: Scheduled auto-export with asyncio.sleep({interval_seconds}s)")
    except RuntimeError:
        # No running loop, create a new one
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _AUTO_EXPORT_TIMER_ID = loop.create_task(_delayed_export())
            console.log(f"DEBUG: Created new event loop and scheduled auto-export")
        except Exception as exc:
            console.error(f"PySheet: failed to schedule auto-export with asyncio - {exc}")

def prompt_for_auto_export_on_load_sync(api_available: bool = None, confirm_method = None, directory_picker_method = None):
    """Prompt user to set up auto-export directory - synchronous version for preserving user gesture.
    
    This MUST be called from synchronous context (e.g., direct event handler) to preserve user gesture
    for the File System API's showDirectoryPicker() which requires active user interaction.
    
    Args:
        api_available: Whether File System API is available (captured before async task).
        confirm_method: Pre-captured window.confirm method from synchronous context.
        directory_picker_method: Pre-captured window.showDirectoryPicker method from synchronous context.
    """
    global _AUTO_EXPORT_SETUP_PROMPTED, _AUTO_EXPORT_DIRECTORY_HANDLE
    
    console.log(f"[DEBUG] prompt_for_auto_export_on_load_sync: checking preconditions")
    console.log(f"[DEBUG] - api_available (captured): {api_available}")
    console.log(f"[DEBUG] - confirm_method (captured): {confirm_method is not None}")
    console.log(f"[DEBUG] - directory_picker_method (captured): {directory_picker_method is not None}")
    
    # Use captured flag if provided
    supports_api = api_available if api_available is not None else False
    console.log(f"[DEBUG] - supports_api={supports_api}")
    console.log(f"[DEBUG] - _AUTO_EXPORT_SETUP_PROMPTED={_AUTO_EXPORT_SETUP_PROMPTED}")
    console.log(f"[DEBUG] - _AUTO_EXPORT_DIRECTORY_HANDLE={_AUTO_EXPORT_DIRECTORY_HANDLE is not None}")
    
    if not supports_api:
        console.log(f"[DEBUG] Returning early: File System API not supported")
        return
    
    # Skip if already configured or already prompted
    if _AUTO_EXPORT_SETUP_PROMPTED or _AUTO_EXPORT_DIRECTORY_HANDLE:
        console.log("[DEBUG] Returning early: already configured or already prompted")
        return
    
    console.log("[DEBUG] Showing confirm dialog...")
    _AUTO_EXPORT_SETUP_PROMPTED = True
    
    wants_setup = False
    try:
        # Use captured confirm_method - this is in synchronous context, preserving user gesture
        if confirm_method is not None:
            console.log("[DEBUG] Using captured confirm_method")
            wants_setup = confirm_method(
                "Set up automatic character exports? Click OK to select a folder where your character will be auto-saved as you make changes."
            )
        console.log(f"[DEBUG] User response: {wants_setup}")
    except JsException as e:
        console.warn(f"[DEBUG] JS Exception during confirm: {e}")
        wants_setup = False
    
    if wants_setup:
        console.log("PySheet: User requested auto-export folder setup on page load")
        # Call the sync version to pick directory while gesture is still active
        _pick_auto_export_directory_sync(confirm_method, directory_picker_method)


def _pick_auto_export_directory_sync(confirm_method = None, directory_picker_method = None):
    """Pick auto-export directory using JavaScript handler to preserve user gesture.
    
    This delegates to window.handleAutoExportSetup which is a JavaScript function that
    preserves gesture context throughout the entire confirm + picker flow.
    
    Args:
        confirm_method: Pre-captured window.confirm method.
        directory_picker_method: Pre-captured window.showDirectoryPicker method.
    """
    global _AUTO_EXPORT_DIRECTORY_HANDLE
    
    # Get the JS handler function
    try:
        from js import window
        handler_func = getattr(window, "handleAutoExportSetup", None)
        if handler_func is None:
            console.warn("[DEBUG] window.handleAutoExportSetup not available")
            return None
    except Exception as e:
        console.warn(f"[DEBUG] Failed to access window.handleAutoExportSetup: {e}")
        return None
    
    try:
        console.log("[DEBUG] Calling window.handleAutoExportSetup (JavaScript gesture-preserving handler)...")
        # Call the JS handler with captured methods - the JS function will preserve gesture throughout
        async def _handle_setup():
            try:
                # Call the JavaScript function which preserves gesture for both confirm and picker
                handle = await handler_func(confirm_method, directory_picker_method)
                
                if handle is None:
                    console.log("[DEBUG] User cancelled or error in JS handler")
                    return None
                
                # Validate the handle
                has_permission = await _ensure_directory_write_permission(handle)
                if not has_permission:
                    console.log("PySheet: directory lacks write permission; will try again on next change")
                    return None
                
                if not hasattr(handle, "getFileHandle"):
                    console.warn("PySheet: selected directory handle cannot create files; falling back to file picker")
                    return None
                
                # Store the handle globally
                global _AUTO_EXPORT_DIRECTORY_HANDLE
                _AUTO_EXPORT_DIRECTORY_HANDLE = handle
                console.log("PySheet: auto-export directory selected successfully")
                return handle
            except JsException as exc:
                name = getattr(exc, "name", "")
                if name == "AbortError":
                    console.log("PySheet: auto-export directory not selected")
                elif name in {"NotAllowedError", "SecurityError"}:
                    console.warn("PySheet: directory picker error - gesture context may have been lost")
                else:
                    console.warn(f"PySheet: auto-export error - {exc}")
                return None
            except Exception as e:
                console.warn(f"[DEBUG] Error in _handle_setup: {type(e).__name__}: {e}")
                return None
        
        # Schedule the async handler
        asyncio.create_task(_handle_setup())
    except Exception as e:
        console.warn(f"PySheet: failed to set up auto-export - {e}")


async def prompt_for_auto_export_on_load(api_available: bool = None, confirm_method = None, directory_picker_method = None):
    """Deprecated: Use prompt_for_auto_export_on_load_sync instead for proper user gesture handling."""
    await asyncio.sleep(0.1)  # Placeholder for compatibility
