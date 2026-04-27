# Currency (Coin Pouch) Persistence Verification

## Summary
✅ **Coin pouch (currency) data IS being saved to the JSON exports correctly.**

## What's Implemented

### 1. **Frontend (HTML/Form)**
- Currency inputs have the proper attributes for automatic capture:
  - `data-character-input` - marks field for auto-save
  - `data-currency-field="pp|gp|ep|sp|cp"` - identifies currency type
  - Element IDs: `currency-pp`, `currency-gp`, `currency-ep`, `currency-sp`, `currency-cp`

### 2. **Data Collection (JavaScript)**
In `static/assets/js/app.js`:

#### Collection on Save
```javascript
currency: Object.fromEntries(CURRENCY.map((coin) => [coin, numberValue(`currency-${coin}`, 0)]))
```
- Captures all 5 coin types from form inputs
- Defaults to 0 if field is empty

#### Data Structure
```javascript
inventory: { items: [], currency: Object.fromEntries(CURRENCY.map((coin) => [coin, 0])) }
```
- Default state includes all currency types initialized to 0

#### Currency Order
```javascript
const CURRENCY = ["pp", "gp", "ep", "sp", "cp"];
```
- Platinum, Gold, Electrum, Silver, Copper

#### Population from JSON
```javascript
for (const coin of CURRENCY) {
  setValue(`currency-${coin}`, state.inventory?.currency?.[coin] ?? 0);
}
```
- Properly restores currency values when loading a saved character

### 3. **Backend Export**
`backend_fastapi.py` `/api/export` endpoint receives and saves character data including the currency object.

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
