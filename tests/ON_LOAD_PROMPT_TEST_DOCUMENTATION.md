# On-Load Auto-Export Prompt - Test Suite Documentation

## Overview

Added comprehensive unit tests for the `prompt_for_auto_export_on_load()` function that prompts users to set up automatic character exports when the page first loads.

## Test File

**Location:** [tests/test_auto_export_on_load_prompt.py](tests/test_auto_export_on_load_prompt.py)

**Total Tests:** 12 (all passing ✓)

## Test Coverage

### 1. Core Prompt Behavior

#### `test_prompt_shown_when_not_configured`
- Verifies that `window.confirm()` is called when auto-export is not yet configured
- Tests the basic prompt display flow
- **Status:** ✓ PASSING

#### `test_prompt_skipped_when_already_configured`
- Verifies that prompt is skipped if auto-export directory already configured
- **Status:** ✓ PASSING

#### `test_prompt_skipped_when_already_prompted`
- Verifies that prompt doesn't appear twice
- Tests the `_AUTO_EXPORT_SETUP_PROMPTED` flag behavior
- **Status:** ✓ PASSING

### 2. User Interaction Paths

#### `test_user_accepts_prompt`
- When user clicks OK on confirm dialog, `_ensure_auto_export_directory()` is called
- Verifies folder picker is triggered with correct parameters
- **Status:** ✓ PASSING

#### `test_user_declines_prompt`
- When user clicks Cancel, `_ensure_auto_export_directory()` is NOT called
- Auto-export setup is deferred (user can still set up manually later)
- **Status:** ✓ PASSING

### 3. Error Handling

#### `test_confirm_throws_js_exception`
- Handles JavaScript exceptions (e.g., SecurityError) from `window.confirm()`
- Gracefully continues when browser blocks confirm dialog
- **Status:** ✓ PASSING

#### `test_ensure_auto_export_directory_exception`
- Handles exceptions thrown by `_ensure_auto_export_directory()`
- Exception caught and logged without propagating
- **Status:** ✓ PASSING

### 4. Edge Cases

#### `test_window_is_none`
- Handles case where `window` object is not available
- Common in non-browser testing environments
- **Status:** ✓ PASSING

#### `test_persistent_export_not_supported`
- Skips prompt when File System API not supported
- Graceful degradation for older browsers
- **Status:** ✓ PASSING

#### `test_prompted_state_set`
- Verifies state tracking after prompting
- Confirms `_AUTO_EXPORT_SETUP_PROMPTED` flag is set
- **Status:** ✓ PASSING

### 5. Integration Tests

#### `test_prompt_scheduled_on_initialization`
- Tests that prompt is properly scheduled during page load
- Verifies `asyncio.create_task()` is used correctly
- **Status:** ✓ PASSING

#### `test_prompt_during_manual_export_prevented`
- Critical: Verifies that `auto=True` flag prevents prompting during delayed auto-export
- This is the fix for the "requires user gesture" issue
- Confirms gesture context loss prevention works
- **Status:** ✓ PASSING

## Key Implementation Details Tested

### Gesture Context Management
```python
# Page load initialization (has gesture context) ✓
async def _prompt_auto_export_on_load():
    from export_management import prompt_for_auto_export_on_load
    await prompt_for_auto_export_on_load()

# Delayed auto-export (NO gesture context) ✓
# The guard `and not auto` prevents prompting
need_prompt = (allow_prompt and not _AUTO_EXPORT_SETUP_PROMPTED and ... and not auto)
```

### State Management
- `_AUTO_EXPORT_SETUP_PROMPTED`: Prevents re-prompting
- `_AUTO_EXPORT_DIRECTORY_HANDLE`: Tracks configured state
- `_AUTO_EXPORT_FILE_HANDLE`: Tracks file access

## Test Results Summary

```
======================== 26 passed, 1 warning in 1.27s ========================
- 14 original auto-export tests: all passing ✓
- 12 new on-load prompt tests: all passing ✓
```

## Running the Tests

```bash
# Run only on-load prompt tests
pytest tests/test_auto_export_on_load_prompt.py -v

# Run all auto-export tests (original + new)
pytest tests/test_auto_export_file_system_api.py tests/test_auto_export_on_load_prompt.py -v

# Run with verbose output
pytest tests/test_auto_export_on_load_prompt.py -v -s
```

## Related Code Changes

### Modified Files
1. **assets/py/export_management.py**
   - Added `prompt_for_auto_export_on_load()` function
   - Modified `_attempt_persistent_export()` with `and not auto` guard
   - Modified `export_character()` for manual export prompting

2. **assets/py/character.py**
   - Added on-load prompt scheduling in initialization block
   - Uses `asyncio.create_task()` for async scheduling

## Architecture

The solution implements a **gesture context-aware** two-phase prompt system:

```
Page Load
  ├─→ Valid user gesture context ✓
  └─→ Prompt: "Set up automatic exports?"
      ├─→ User clicks OK → Folder picker appears
      └─→ User clicks Cancel → Deferred to manual export

Manual Export (Button Click)
  ├─→ Valid user gesture context ✓
  └─→ Auto-export directory setup allowed (if first time)

Delayed Auto-Export (asyncio.sleep(2.0))
  ├─→ NO user gesture context ✗
  └─→ Never prompt (uses already-configured handles)
```

## Verification

✓ All 26 tests passing (100% success rate)
✓ No syntax errors
✓ No import issues
✓ Full coverage of on-load prompt lifecycle
✓ Integration with existing auto-export tests verified
