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
    from js import window, document, setTimeout, clearTimeout, localStorage, fetch, Blob, URL, FileReader
    from pyodide import create_proxy, JsException
except ImportError:
    # Non-PyScript environment (testing)
    window = None
    document = None
    setTimeout = None
    clearTimeout = None
    localStorage = None
    fetch = None
    Blob = None
    URL = None
    FileReader = None
    create_proxy = lambda x: x
    JsException = Exception

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

_AUTO_EXPORT_TIMER_ID: Optional[int] = None
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
    """Return callable setTimeout/clearTimeout, preferring globals then window/js."""
    try_set = setTimeout
    try_clear = clearTimeout

    # Prefer window methods if globals are missing
    if (try_set is None or try_clear is None) and window is not None:
        try_set = try_set or getattr(window, "setTimeout", None)
        try_clear = try_clear or getattr(window, "clearTimeout", None)

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
    
    Format: <name>_<class>_lvl<level>_YYYYMMDD_HHMM.json
    Only works if directory_handle supports async iteration (desktop/Chrome).
    """
    if directory_handle is None:
        return
    
    try:
        cutoff_date = datetime.now() - timedelta(days=EXPORT_PRUNE_DAYS)
        pruned_count = 0
        
        # Attempt to iterate and delete old files
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
                    if file_date < cutoff_date:
                        await directory_handle.removeEntry(entry.name)
                        pruned_count += 1
                        console.log(f"PySheet: pruned old export {entry.name}")
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
                        if file_date < cutoff_date:
                            await directory_handle.removeEntry(entry_name)
                            pruned_count += 1
                            console.log(f"PySheet: pruned old export {entry_name}")
                    except (ValueError, JsException):
                        continue
            except (AttributeError, JsException):
                pass
        
        if pruned_count > 0:
            console.log(f"PySheet: pruned {pruned_count} exports older than {EXPORT_PRUNE_DAYS} days")
    
    except Exception as exc:
        console.warn(f"PySheet: error during export pruning: {exc}")


# ===================================================================
# File System API Helpers
# ===================================================================

async def _ensure_directory_write_permission(handle) -> bool:
    """Check/request write permission for directory handle."""
    if handle is None or window is None:
        return False
    
    query_permission = getattr(handle, "queryPermission", None)
    request_permission = getattr(handle, "requestPermission", None)
    if query_permission is None or request_permission is None:
        return True
    
    try:
        status = await query_permission({"mode": "readwrite"})
    except JsException as exc:
        console.warn(f"PySheet: directory permission query failed - {exc}")
        status = None
    
    if status == "granted":
        return True
    if status == "denied":
        return False
    
    try:
        status = await request_permission({"mode": "readwrite"})
    except JsException as exc:
        console.warn(f"PySheet: directory permission request failed - {exc}")
        return False
    
    return status == "granted"


def _ensure_auto_export_proxy():
    """Create or retrieve the auto-export callback proxy."""
    global _AUTO_EXPORT_PROXY
    if _AUTO_EXPORT_PROXY is None and window is not None:
        def _auto_export_callback(*_args):
            global _AUTO_EXPORT_TIMER_ID
            _AUTO_EXPORT_TIMER_ID = None
            
            async def _run_auto_export():
                global _AUTO_EXPORT_EVENT_COUNT
                try:
                    await export_character(auto=True)
                except Exception as exc:
                    console.error(f"PySheet: auto-export failed - {exc}")
                finally:
                    _AUTO_EXPORT_EVENT_COUNT = 0

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_run_auto_export())
            except RuntimeError:
                asyncio.run(_run_auto_export())
        
        _AUTO_EXPORT_PROXY = create_proxy(_auto_export_callback)
        _EVENT_PROXIES.append(_AUTO_EXPORT_PROXY)
    
    return _AUTO_EXPORT_PROXY


def _supports_persistent_auto_export() -> bool:
    """Check if browser supports File System API for persistent exports."""
    if window is None:
        return False
    return bool(
        hasattr(window, "showDirectoryPicker")
        or hasattr(window, "showSaveFilePicker")
    )


async def _ensure_auto_export_directory(auto_trigger: bool = True):
    """Prompt user to select directory for auto-export."""
    global _AUTO_EXPORT_DIRECTORY_HANDLE, _AUTO_EXPORT_DISABLED
    if _AUTO_EXPORT_DIRECTORY_HANDLE is not None or window is None:
        return _AUTO_EXPORT_DIRECTORY_HANDLE if _AUTO_EXPORT_DIRECTORY_HANDLE is not None else None
    
    if not hasattr(window, "showDirectoryPicker"):
        return None
    
    try:
        handle = await window.showDirectoryPicker()
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
    """Prompt user to select file for auto-export."""
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
        writable = await handle.createWritable()
        await writable.write(payload)
        await writable.close()
    except JsException as exc:
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

    need_prompt = (
        allow_prompt
        and not _AUTO_EXPORT_SETUP_PROMPTED
        and _AUTO_EXPORT_DIRECTORY_HANDLE is None
        and _AUTO_EXPORT_FILE_HANDLE is None
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

    if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
        try:
            file_handle = await _AUTO_EXPORT_DIRECTORY_HANDLE.getFileHandle(
                proposed_filename,
                {"create": True},
            )
        except JsException as exc:
            console.warn(f"PySheet: unable to open auto-export file in directory ({exc})")
            if auto:
                _AUTO_EXPORT_DIRECTORY_HANDLE = None
        else:
            try:
                await _write_auto_export_file(file_handle, payload)
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


def cleanup_exports(_event=None):
    """Clean up old export files (browser-based pruning of localStorage info)."""
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
    global _LAST_AUTO_EXPORT_SNAPSHOT, _LAST_AUTO_EXPORT_DATE, _AUTO_EXPORT_FILE_HANDLE
    global _AUTO_EXPORT_DISABLED, _AUTO_EXPORT_SUPPORT_WARNED, _AUTO_EXPORT_DIRECTORY_HANDLE
    global _AUTO_EXPORT_LAST_FILENAME, _AUTO_EXPORT_SETUP_PROMPTED
    
    storage = _resolve_local_storage()
    if window is None or document is None or storage is None:
        return

    def show_saving_state():
        """Show green SAVING state."""
        indicator = document.getElementById("saving-indicator")
        if indicator:
            indicator.classList.remove("recording", "fading")
            indicator.classList.add("saving")
            indicator.style.display = "flex"
            indicator.style.opacity = "1"

    def fade_indicator():
        """Fade to gray and remove."""
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

                if setTimeout is not None:
                    proxy = create_proxy(_hide_after_fade)
                    _EVENT_PROXIES.append(proxy)
                    setTimeout(proxy, 1200)
                else:
                    indicator.style.display = "none"
            except Exception as exc:
                console.warn(f"[DEBUG][export] unable to hide saving-indicator: {exc}")

    character_module = _get_character_module()
    collect_character_data = getattr(character_module, "collect_character_data", None) if character_module else None
    if collect_character_data is None:
        console.error("PySheet: export failed before write - collect_character_data unavailable")
        fade_indicator()
        return

    try:
        data = collect_character_data()
        payload = json.dumps(data)
    except Exception as exc:
        console.error(f"PySheet: export failed before write - {exc}")
        fade_indicator()
        return
    
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
    
    show_saving_state()

    now = datetime.now()
    proposed_filename = _build_export_filename(data, now=now)

    persistent_used = await _attempt_persistent_export(
        payload,
        proposed_filename,
        auto=auto,
        allow_prompt=not _AUTO_EXPORT_SETUP_PROMPTED,
    )
    if persistent_used:
        fade_indicator()
        return

    if auto:
        if not _supports_persistent_auto_export():
            if not _AUTO_EXPORT_SUPPORT_WARNED:
                console.warn("PySheet: browser does not support persistent auto-export; using fallback downloads")
                _AUTO_EXPORT_SUPPORT_WARNED = True
        elif not (_AUTO_EXPORT_DIRECTORY_HANDLE or _AUTO_EXPORT_FILE_HANDLE):
            console.log("PySheet: auto-export not yet configured; will try again on next change")
            fade_indicator()
            return
        else:
            fade_indicator()
            return

    # Fallback: download via browser
    if Blob is not None and URL is not None:
        try:
            blob = Blob.new([payload], {"type": "application/json"})
            url = URL.createObjectURL(blob)
            link = document.createElement("a")
            link.href = url
            link.download = proposed_filename
            link.click()
            URL.revokeObjectURL(url)
            _LAST_AUTO_EXPORT_SNAPSHOT = payload
            _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
            if auto:
                console.log(f"PySheet: auto-exported character JSON (download) to {proposed_filename}")
            else:
                console.log(f"PySheet: exported character JSON to {proposed_filename}")
        except Exception as exc:
            console.error(f"PySheet: export failed - {exc}")
    
    fade_indicator()


def reset_character(_event=None):
    """Reset character to default state."""
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
        
        # Attach the callback
        load_proxy = create_proxy(on_load)
        _EVENT_PROXIES.append(load_proxy)
        reader.onload = load_proxy
        console.log("[IMPORT] Callback attached, reading file...")
        reader.readAsText(file_obj)
        
    except Exception as e:
        console.error(f"[IMPORT] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


def schedule_auto_export():
    """Schedule automatic character export with debouncing.
    
    Always saves to localStorage immediately to preserve data across page refreshes.
    Also schedules an async export if browser supports File System API and user configured it.
    """
    global _AUTO_EXPORT_TIMER_ID, _AUTO_EXPORT_EVENT_COUNT
    storage = _resolve_local_storage()

    # If this module was imported in a non-browser context (e.g. test harness) but later
    # executed in PyScript, try to re-hydrate the browser globals before bailing.
    if window is None or document is None:
        try:  # noqa: SIM105 - explicit rebind of globals is intentional
            from js import window as js_window, document as js_document, setTimeout as js_setTimeout, clearTimeout as js_clearTimeout  # type: ignore

            globals()["window"] = js_window
            globals()["document"] = js_document
            if setTimeout is None:
                globals()["setTimeout"] = js_setTimeout
            if clearTimeout is None:
                globals()["clearTimeout"] = js_clearTimeout
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
    if indicator:
        indicator.classList.remove("saving", "fading")
        indicator.classList.add("recording")
        # Force visibility in cases where CSS hasn't applied yet
        indicator.style.display = "flex"
        indicator.style.opacity = "1"
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
    
    proxy = _ensure_auto_export_proxy()

    timer_set, timer_clear = _resolve_timers()
    if timer_set is None:
        console.warn("[DEBUG][auto-export] setTimeout unavailable; skipping schedule")
        return

    if _AUTO_EXPORT_TIMER_ID is not None and timer_clear is not None:
        timer_clear(_AUTO_EXPORT_TIMER_ID)
    remaining = AUTO_EXPORT_MAX_EVENTS - _AUTO_EXPORT_EVENT_COUNT
    interval = AUTO_EXPORT_DELAY_MS
    if remaining <= 0:
        interval = int(AUTO_EXPORT_DELAY_MS * 0.25)
    _AUTO_EXPORT_TIMER_ID = timer_set(proxy, interval)
