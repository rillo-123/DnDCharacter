# Currency Button Controls Implementation

## Summary
Added ±10 and ±100 adjustment buttons to the Coin Pouch table for quick currency adjustments.

## Changes Made

### 1. **HTML Structure** (`static/index.html`)
- Added a new "Adjust" column in the currency table header
- Added 4 buttons per coin type (in a buttons cell):
  - `-100` button (red)
  - `-10` button (red)
  - `+10` button (green)
  - `+100` button (green)
- Each button has:
  - `data-currency="pp|gp|ep|sp|cp"` - identifies the currency type
  - `data-amount="-100|-10|10|100"` - the adjustment amount
  - `class="currency-btn currency-btn-plus|minus"` - styling classes
  - `title` attribute for hover tooltips

### 2. **CSS Styling** (`static/assets/css/styles.css`)
Added comprehensive styling for the currency buttons:
- `.currency-buttons` - flex container for button layout
- `.currency-btn` - base button styling with dark theme
- `.currency-btn:hover` - hover effect (blue highlight)
- `.currency-btn:active` - click effect
- `.currency-btn-minus` - red styling for subtract buttons
- `.currency-btn-plus` - green styling for add buttons

**Features:**
- Dark mode compatible
- Smooth transitions on hover and click
- Color-coded (red for minus, green for plus)
- Responsive layout with flex wrapping

### 3. **Event Handler** (`static/assets/py/character.py`)

#### New Function: `handle_currency_button(event)`
- Extracts currency type and adjustment amount from button attributes
- Gets current currency value from form input
- Adds adjustment amount to current value
- Prevents negative values (max(0, new_value))
- Updates the form value
- Triggers calculations and auto-export

#### Modified: `register_event_listeners()`
- Added registration for all `.currency-btn` buttons
- Creates event proxies for each button
- Attaches click listeners that call `handle_currency_button()`

## User Experience

### How It Works:
1. Click any adjustment button next to a currency type
2. The value in the input field instantly updates
3. Character auto-saves with the new value
4. If the result would be negative, it stays at 0

### Example Usage:
- Click `+100` next to Gold (GP) → adds 100 gold to current amount
- Click `-10` next to Copper (CP) → subtracts 10 copper (but not below 0)
- Click `+10` multiple times → adds 10 each click (cumulative)

## Testing
✅ All existing tests pass (18 character export tests)
✅ All currency persistence tests pass (9 tests)
✅ Python syntax verified
✅ HTML structure verified (20 button elements found)

## Files Modified
- `static/index.html` - Added button column and 20 buttons (5 rows × 4 buttons)
- `static/assets/css/styles.css` - Added 50+ lines of button styling
- `static/assets/py/character.py` - Added event handler and registration (40+ lines)
