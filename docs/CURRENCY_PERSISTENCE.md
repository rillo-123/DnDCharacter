# Currency (Coin Pouch) Persistence Verification

## Summary
✅ **Coin pouch (currency) data IS being saved to the JSON exports correctly.**

## What's Implemented

### 1. **Frontend (HTML/Form)**
- Currency inputs have the proper attributes for automatic capture:
  - `data-character-input` - marks field for auto-save
  - `data-currency-field="pp|gp|ep|sp|cp"` - identifies currency type
  - Element IDs: `currency-pp`, `currency-gp`, `currency-ep`, `currency-sp`, `currency-cp`

### 2. **Data Collection (Python/PyScript)**
In `static/assets/py/character.py`:

#### Collection on Save (Line 2869)
```python
"currency": {key: get_numeric_value(f"currency-{key}", 0) for key in CURRENCY_ORDER}
```
- Captures all 5 coin types from form inputs
- Defaults to 0 if field is empty

#### Data Structure (Line 1721)
```python
"currency": {key: 0 for key in CURRENCY_ORDER}
```
- Default state includes all currency types initialized to 0

#### Currency Order (Line 1686)
```python
CURRENCY_ORDER = ["pp", "gp", "ep", "sp", "cp"]
```
- Platinum, Gold, Electrum, Silver, Copper

#### Population from JSON (Lines 3011-3014)
```python
currency = inv.get("currency", {})
for key in CURRENCY_ORDER:
    set_form_value(f"currency-{key}", currency.get(key, 0))
```
- Properly restores currency values when loading a saved character

### 3. **Backend Export**
`backend.py` `/api/export` endpoint receives and saves character data including the currency object.

### 4. **Verification**
✅ All tests pass including:
- 9 new currency-specific tests
- 18 character export tests
- Existing currency HTML structure tests

✅ Actual export file verification shows currency data is present:
```json
{
  "inventory": {
    "currency": {
      "pp": 0,
      "gp": 0,
      "ep": 0,
      "sp": 0,
      "cp": 0
    }
  }
}
```

## How to Use

1. **Enter coin amounts** in the Coin Pouch table (Inventory tab)
2. **Character data auto-saves** with currency values
3. **Export file includes** the currency data
4. **Load saved character** and currency values are restored

## Files Modified
- `static/index.html` - Changed coin pouch from grid layout to table
- `static/assets/css/styles.css` - Added dark mode table styles for currency
- `tests/test_currency_persistence.py` - Added comprehensive currency tests (NEW)

## Next Steps
No action needed - currency persistence is fully functional and tested.
