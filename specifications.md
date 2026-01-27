# D&D Character Sheet Application - Specifications

## Project Overview

A comprehensive web-based D&D 5e character sheet application with inventory management, equipment tracking, autosave functionality, and export/import capabilities.

## Technology Stack

- **Backend:** Python (Pyodide for WASM execution in browser)
- **Frontend:** HTML5, CSS3, JavaScript
- **Data Format:** JSON
- **Storage:** Browser localStorage + file exports

## Core Features

### 1. Character Management

#### Ability Scores
- Strength (STR)
- Dexterity (DEX)
- Constitution (CON)
- Intelligence (INT)
- Wisdom (WIS)
- Charisma (CHA)

Abilities support:
- Base scores (8-20 range)
- Race bonuses
- Ability modifiers (auto-calculated)
- Saves (with proficiency support)
- Skills derived from abilities

#### Character Stats
- Hit Points (HP)
- Armor Class (AC)
- Level (1-20)
- Experience Points
- Proficiency Bonus (auto-calculated from level)
- Speed
- Initiative

### 2. Armor Class (AC) System

#### AC Calculation Rules (D&D 5e)

**No Armor:**
```
AC = 10 + DEX modifier
```

**Light Armor:**
```
AC = Base AC + full DEX modifier
Base AC values: Leather (11), Studded Leather (12), Hide (12), Chain Shirt (13)
```

**Medium Armor:**
```
AC = Base AC + DEX modifier (capped at +2)
Base AC values: Scale Mail (14), Breastplate (14), Half Plate (15)
```

**Heavy Armor:**
```
AC = Base AC (no DEX modifier added)
Base AC values: Chain Mail (16), Splint (17), Plate (18)
```

**Shields:**
```
Shield Bonus (added to total AC):
- Normal Shield: +2
- Shield +1: +3 (base 2 + magic bonus 1)
- Shield +2: +4 (base 2 + magic bonus 2)
- etc.
```

#### AC in Combat Tab
Total AC displayed = Armor AC + DEX modifier + Shield bonus + any item modifiers

#### AC with Bonuses
When adding a magic bonus to armor:
- User specifies bonus value (e.g., "+1")
- Armor AC = Base armor AC + bonus value
- Breastplate +1 = 14 + 1 = 15 base AC
- Final AC in combat = 15 + DEX modifier + shield bonus

### 3. Inventory Management

#### Inventory System

**Item Categories:**
- Armor (includes shields)
- Weapons
- Adventuring Gear

**Item Properties:**
- Name
- Quantity
- Weight
- Cost
- Equipped status
- Notes (JSON format for extra properties)
- Source (where acquired)

**Item Notes Format (JSON):**

For Regular Armor:
```json
{
  "armor_class": "14",
  "armor_type": "medium",
  "bonus": 0
}
```

For Magic Armor (e.g., +1 Breastplate):
```json
{
  "armor_class": 15,
  "armor_type": "medium",
  "bonus": 1
}
```

For Shields:
```json
{
  "bonus": 3,
  "armor_type": "Shield"
}
```

For Weapons:
```json
{
  "damage": "1d8",
  "damage_type": "slashing",
  "properties": "finesse, light"
}
```

### 4. Equipment Management

#### Open5e Integration
- Browse weapons and armor from Open5e database
- Add items with automatic property detection
- Store items in equipment.json database

#### Equipment Database
- Location: `assets/py/equipment_data.py`
- Stores commonly used weapons, armor, and magic items
- Supports direct item addition or browsing

#### Equipment Import
- Import from Open5e API
- Store to local equipment database
- Auto-categorization based on item properties

### 5. Character Export/Import

#### Export Format
- JSON format
- Complete character state preservation
- Timestamped file naming: `{CharacterName}_{Class}_lvl{Level}_{Date}_{Time}.json`
- Located in `exports/` directory

#### Export Contents
- Character name, class, level
- Ability scores
- Skills and proficiencies
- Inventory (all items with notes)
- Spells (if applicable)
- Class-specific features
- Character appearance/background

#### Autosave System
- Triggers on specific events:
  - Ability score changes
  - Equipment modifications
  - Inventory changes
  - Spell slot usage
  - Character state updates
- Maximum 100 autosaves per session
- Automatic cleanup of old autosaves

### 6. Armor System Architecture

#### Armor Entity Class
Properties and methods for individual armor items:
- `_calculate_ac()` - Calculates final AC based on armor type and DEX
- `final_armor_type` - Determines armor classification
- `final_material` - Tracks armor material
- Stealth implications (heavy armor disadvantage)

#### Armor Manager
- Manages all equipped armor and shields
- Renders armor table in character sheet
- Handles armor bonus calculations
- Separates armor AC display from shield bonuses

#### Armor Collection Manager
- Manages multiple armor instances
- Renders armor grid/table
- Synchronizes with inventory

#### Armor Type Classification
```
Light Armor:
  - Leather, Studded Leather, Hide, Chain Shirt

Medium Armor:
  - Scale Mail, Breastplate, Half Plate

Heavy Armor:
  - Chain Mail, Splint, Plate
  - Requires STR 15+, causes Stealth disadvantage
```

### 7. Weapon System

#### Weapon Properties
- Damage dice (e.g., 1d8, 2d6)
- Damage type (slashing, piercing, bludgeoning, etc.)
- Weapon properties (finesse, light, heavy, range, etc.)
- Attack bonus (STR or DEX + proficiency if applicable)

#### Weapon Table
- Displays equipped weapons
- Shows attack bonuses with ability scorer modifiers + proficiency
- Armor items filtered out (cannot appear in weapons table)

#### Damage Calculation
- Base damage = damage dice
- Ability modifier (STR for melee, DEX for finesse/ranged)
- Proficiency bonus (if proficient)
- Magic item bonuses

### 8. Skills System

#### Skill Checks
- 18 D&D 5e skills derived from ability scores
- Proficiency tracking
- Jack of All Trades (Bard feature)
- Expertise (double proficiency)

#### Skill Formula
```
Skill = Ability Modifier ± Proficiency (if proficient) ± Items
```

### 9. Save System

#### Ability Saves
- Calculated for each ability
- Proficiency bonus if proficient
- Magic item modifiers supported

#### Save Tooltip
Shows breakdown:
- Ability modifier
- Proficiency (if applicable)
- Item modifiers

### 10. Data Storage

#### Browser Storage
- Key: `pysheet.character.v1`
- Format: JSON serialized character data
- Auto-updated on autosave

#### File Export
- Location: `exports/` folder
- Format: .json files
- Unlimited storage (user filesystem)

#### Autosave Storage
- Location: `exports/autosaves/` folder
- Format: `.json` files per autosave
- Cleanup: Keeps last 100 autosaves

## Architecture Patterns

### 1. Manager Pattern
- `InventoryManager` - Manages all inventory items
- `ArmorManager` - Manages armor-specific logic
- `EquipmentManager` - Handles item bonuses and modifications

### 2. Entity Pattern
- `ArmorEntity` - Represents individual armor items
- Properties and calculation methods encapsulated

### 3. Proxy Pattern
- Used in equipment management for safe data access
- Prevents unintended mutations

## Known Issues & Constraints

### Armor Type Detection
- Requires `armor_type` in notes for proper DEX modifier application
- Auto-detected when armor imported from equipment database

### Shield Bonus Format (Legacy)
- Old format stored bonus as magic bonus only (1 for +1 shield)
- New format stores total bonus (3 for +1 shield = base 2 + magic 1)
- System handles both formats for backward compatibility

### AC Calculation
- Shield bonuses are separate from armor AC display
- Each component (armor, DEX, shield) shown individually in combat tab

## GUI / User Interface

The character sheet is organized into seven tabs, each containing one or two card sections with related content. The interface uses a clean, modern design with bordered cards on a subtle background.

### Overview Tab

The Overview tab presents essential character information and ability scores in two side-by-side cards.

#### Card 1: Character Information

This card displays a labeled two-column table containing all core character details. The table has alternating row styling for readability, with labels in the left column and input fields or dropdowns in the right column.

**Graphical Elements:**
- **Character Name Input**: A text input field at the top of the table. Styled with standard input appearance, placeholder text shows example names. Behavior: Editable text field that triggers autosave on change.
- **Class Dropdown**: A select element with options for all D&D 5e classes (Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard). Styled as a standard HTML select with browser-default appearance. Behavior: Changes affect spell slots, proficiency bonus calculations, and available features.
- **Race Dropdown**: A select element with common D&D races (Human, Elf, Dwarf, Halfling, Dragonborn, Gnome, Half-Elf, Half-Orc, Tiefling). Behavior: Affects ability score bonuses automatically.
- **Background Dropdown**: A select element with D&D backgrounds (Acolyte, Charlatan, Criminal, Entertainer, Folk Hero, Guild Artisan, Hermit, Noble, Outlander, Sage, Sailor, Soldier, Urchin). Behavior: Informational selection, doesn't trigger calculations.
- **Domain Dropdown**: A select element specific to Clerics with domain options (Arcana, City, Death, Forge, Grave, Knowledge, Life, Light, Nature, Order, Peace, Tempest, Trickery, War). Behavior: Affects available spells and features.
- **Alignment Dropdown**: A select element with all nine D&D alignments (Lawful Good through Chaotic Evil). Behavior: Informational only, no mechanical effects.
- **Player Name Input**: Text input field for the actual player's name. Behavior: Stores player information, no mechanical effects.
- **Level Input**: Number input with min="1" max="20". Styled as a spinner control with up/down arrows. Behavior: Directly affects proficiency bonus (auto-calculated), hit points, spell slots, and class features. Changes trigger recalculation of multiple derived values.
- **Proficiency Bonus Output**: A read-only output element showing calculated proficiency (e.g., "+2", "+3"). Styled in bold. Behavior: Automatically calculated as floor((level - 1) / 4) + 2, updates immediately when level changes.

#### Card 2: Ability Scores

This card contains a comprehensive ability scores table with seven columns showing all six ability scores (STR, DEX, CON, INT, WIS, CHA) in rows. The table uses a grid layout optimized for quick scanning and editing.

**Graphical Elements:**
- **Table Header**: Labels for "Ability", "Score", "Race", "Total", "Bonus", "Save", and "Prof". Styled with bold text and subtle bottom border.
- **Ability Label Column**: Six cells showing three-letter ability abbreviations (STR, DEX, CON, INT, WIS, CHA) in bold uppercase text.
- **Score Input Column**: Number inputs with min="1" max="30", default="10". Styled as compact number spinners. Behavior: Triggers recalculation of Total, Bonus, Save, and all dependent skills. Valid range is 1-30 per D&D rules.
- **Race Bonus Column**: Read-only span elements showing racial bonuses (e.g., "+2", "+1", or "—" for none). Styled in a muted text color. Behavior: Automatically populated based on selected race, cannot be manually edited.
- **Total Column**: Read-only span elements showing Score + Race bonus. Styled in bold. Behavior: Automatically calculated, updates when Score or Race changes.
- **Bonus Column**: Read-only span elements showing ability modifiers (e.g., "+3", "+0", "-1"). Calculated as floor((Total - 10) / 2). Styled with color coding: green for positive, gray for zero, red for negative. Behavior: Updates automatically, used in all skill and save calculations.
- **Save Column**: Read-only span elements showing saving throw bonuses (e.g., "+5"). Calculated as Bonus + (Proficiency Bonus if Prof checked). Styled in bold. Behavior: Updates when ability changes or proficiency is toggled.
- **Prof Column**: Checkboxes for marking saving throw proficiency. Standard checkbox appearance. Behavior: When checked, adds proficiency bonus to the save total. Typically 2-3 abilities are proficient based on class.

### Equipment Tab

The Equipment tab provides equipment management through two cards: a searchable equipment library on the left and the character's current inventory with currency on the right.

#### Card 1: Equipment Library

This card presents a searchable database of equipment items from the Open5e API. The card has a white background with subtle border and padding.

**Graphical Elements:**
- **Search Input**: A text input field at the top with placeholder "Search equipment...". Styled with left padding for visual balance. Behavior: Real-time search that filters equipment list as you type, queries Open5e database after short debounce delay.
- **Equipment Results List**: A scrollable div containing equipment cards. Each card shows: item name (bold header), AC or damage value (if applicable), properties list (comma-separated), weight and cost (small gray text at bottom). Styled with light background, border, padding, and hover effect (slight shadow increase). Maximum height with scroll overflow.
- **Add Button**: A small button on each equipment card labeled "Add". Styled as a primary action button with blue background. Behavior: Clicking adds the item to the character's inventory, triggers equipment_management functions, updates the inventory list immediately.
- **Category Pills**: Filter buttons for "All", "Weapons", "Armor", "Adventuring Gear". Styled as pill-shaped buttons, active one highlighted in blue. Behavior: Filters the equipment results to show only matching category.
- **Loading Indicator**: A subtle text or spinner shown during API requests. Styled with gray animated text. Behavior: Appears during fetch, disappears when results load.

#### Card 2: Equipment & Wealth

This card shows the character's current inventory as a list of items, followed by a currency table. The card has a dark blue background with subtle border. 

**Graphical Elements:**
- **Inventory List**: A vertical list of inventory items, each displayed as a row with: checkbox (equipped status), item name (bold), category badge (colored pill), quantity (small), weight, cost, and action buttons. Styled with hover effect and subtle borders between items.
- **Equipped Checkbox**: A checkbox at the start of each row. Standard checkbox appearance. Behavior: When checked, the item is marked as equipped and affects character stats (armor AC, weapon attacks). Unchecking removes the item's effects. Only one armor can be equipped at a time; checking a new armor automatically unequips the previous one.
Shields and other add-on armor items can be equipped together with armor. They contribute to the total AC for the character.
- **Item Name**: Text display showing the item name in bold. Behavior: Click to edit in a modal (future enhancement).
- **Category Badge**: A small colored pill showing item category ("Weapon", "Armor", "Gear"). Styled with category-specific colors: red for weapons, blue for armor, gray for gear.
- **Quantity Display**: Small gray text showing item count (e.g., "×3"). Behavior: Can be incremented/decremented via buttons (not yet implemented in current UI).
- **Weight and Cost**: Small gray text at the end of each row showing individual item weight and cost.
- **Delete Button**: A small red "×" button on the right side of each row. Behavior: Removes the item from inventory after confirmation, triggers inventory update.
- **Currency Table**: A four-column table showing currency types (Copper, Silver, Electrum, Gold, Platinum) with input fields for each. Styled with alternating row colors and compact layout.
- **Currency Inputs**: Number inputs with min="0" for each currency type. Styled as compact inputs. Behavior: Triggers autosave on change, used for tracking character wealth. No automatic conversion between denominations.
- **Total Weight Display**: A summary line below the inventory showing total carried weight. Styled in bold. Behavior: Automatically sums all equipped and carried items, updates when inventory changes.

### Skills Tab

The Skills tab presents skill proficiencies and passive perception on the left, with equipped weapons and armor tables on the right.

#### Card 1: Skills & Passive Perception

This card contains a comprehensive skills table listing all 18 D&D 5e skills with proficiency and expertise options, followed by a passive perception display.

**Graphical Elements:**
- **Skills Table**: A five-column table with headers "Skill", "Bonus", "Prof", "Exp", "Ability". Each row represents one skill. Styled with alternating row backgrounds for readability, compact row height.
- **Skill Name Column**: Text labels for each skill (Acrobatics, Animal Handling, Arcana, Athletics, Deception, History, Insight, Intimidation, Investigation, Medicine, Nature, Perception, Performance, Persuasion, Religion, Sleight of Hand, Stealth, Survival). Styled in regular weight.
- **Bonus Column**: Read-only spans showing calculated skill modifier (e.g., "+5", "+0", "-1"). Calculated as Ability Modifier + (Proficiency Bonus if Prof) + (Proficiency Bonus again if Exp). Styled in bold. Behavior: Updates automatically when ability scores, proficiency, or expertise changes.
- **Prof Checkbox Column**: Standard checkboxes for marking skill proficiency. Behavior: When checked, adds proficiency bonus to skill total. Typical characters have 4-6 skills proficient.
- **Exp Checkbox Column**: Standard checkboxes for marking expertise. Behavior: When checked (requires Prof also checked), doubles proficiency bonus for that skill. Expertise is a class feature for Rogues and Bards.
- **Ability Column**: Small gray text showing which ability the skill uses (STR, DEX, INT, WIS, CHA). Read-only, informational.
- **Passive Perception Display**: A derived metric box below the table showing "Passive Perception" label and calculated value (10 + Perception bonus). Styled with larger bold number in a bordered box. Behavior: Auto-calculated, updates when Perception skill or WIS changes. Used by DM for detecting hidden creatures/traps.

#### Card 2: Weapons & Armor

This card displays two tables: equipped weapons at the top and equipped armor at the bottom. Both tables show only equipped items from the inventory.

**Graphical Elements:**
- **Weapons Table**: A five-column table with headers "Weapon", "To Hit", "Damage", "Range", "Properties". Shows all equipped weapons.
- **Weapon Name Column**: Text display of weapon name. Styled in regular weight.
- **To Hit Column**: Read-only span showing attack bonus (e.g., "+7"). Calculated as relevant ability modifier (STR for melee, DEX for ranged/finesse) + proficiency bonus (if proficient). Styled in bold. Behavior: Updates when ability scores or proficiency changes.
- **Damage Column**: Text showing damage dice and type (e.g., "1d8+4 slashing"). Calculated as weapon dice + ability modifier. Behavior: Updates when ability scores change.
- **Range Column**: Text showing weapon range (e.g., "80/320" for ranged, "5 ft." for melee). Read-only, from weapon properties.
- **Properties Column**: Comma-separated list of weapon properties (Finesse, Light, Versatile, etc.). Text wraps if needed. Read-only.
- **Empty State**: If no weapons equipped, shows centered message "No weapons equipped. Add weapons from your equipment inventory." Styled in gray italic text.
- **Armor Table**: A six-column table with headers "Armor", "AC", "Type", "Material", "Stealth", "Equipped". Shows all armor and shields in inventory (not just equipped ones).
- **Armor Name Column**: Text display of armor/shield name. Shields shown with green text color to differentiate.
- **AC Column**: For armor, shows armor's AC value (base + magical bonus). For shields, shows AC bonus with "+" prefix (e.g., "+2" for normal shield, "+3" for Shield +1). Styled in bold. Behavior: Used in AC calculation, updates from item properties.
- **Type Column**: Text showing armor type (Light, Medium, Heavy) or "Shield". Color-coded: Light (green), Medium (blue), Heavy (red), Shield (green).
- **Material Column**: Text showing armor material (Leather, Chain Mail, Plate, Steel, etc.). Read-only from item data.
- **Stealth Column**: Text showing "Disadvantage" for heavy armor, "Normal" otherwise. Styled in red if disadvantage. Behavior: Informational for DM and player.
- **Equipped Column**: Checkbox indicating if this armor/shield is currently equipped. Behavior: Checking equips the item, affecting AC calculation. Only one armor can be equipped at a time; checking a new armor automatically unequips the previous one. Shields can be equipped alongside armor. Unchecking removes the item's effects from character stats.
- **Empty State**: If no armor in inventory, shows centered message "No armor in inventory. Add armor from the Equipment tab." Styled in gray italic text.

### Combat Tab

The Combat tab consolidates all combat-related statistics and health management in a single card with a two-column layout.

#### Card 1: Combat Stats & Health Management

This card uses a two-column grid layout. The left column shows combat statistics in a table, while the right column contains health management controls and proficiency displays.

**Left Column: Combat Stats**

**Graphical Elements:**
- **Combat Stats Table**: A two-column table with labels in the left column and values in the right. Styled with subtle row borders and compact padding.
- **Armor Class Row**: Label "Armor Class" with large bold AC value (e.g., "17"). Value styled prominently with larger font. Behavior: Displays calculated AC with tooltip showing breakdown (Base AC + DEX mod + Shield + bonuses). Tooltip appears on hover.
- **Initiative Row**: Label "Initiative" with calculated bonus (e.g., "+3"). Behavior: Shows DEX modifier, used for combat turn order.
- **Speed Row**: Label "Speed" with value in feet (e.g., "30 ft."). Behavior: Editable or calculated based on race/armor penalties.
- **Proficiency Bonus Row**: Label "Proficiency Bonus" with calculated value (e.g., "+3"). Read-only, derived from level.
- **Perception/Insight/Investigation Row**: Three passive skills shown in one row with labels and values. Styled as smaller text. Behavior: Auto-calculated from respective skill bonuses, used for passive checks.

**Right Column: Health Management**

**Graphical Elements:**
- **Hit Points Section**: A health group with header "Hit Points", current/max display, and adjustment buttons.
- **HP Display**: Large bold numbers showing "Current / Max" (e.g., "45 / 58"). Styled prominently at top of section. Behavior: Updates in real-time as buttons are clicked.
- **Current HP Input**: Number input showing current hit points. Behavior: Can be manually edited, clamped between 0 and max HP.
- **Max HP Input**: Number input showing maximum hit points. Behavior: Editable, used as upper bound for current HP.
- **HP Adjustment Buttons**: A row of buttons labeled "-10", "-5", "-1", "+1", "+5", "+10", "Set to Max". Styled as compact buttons in a flex row. Behavior: Click to adjust current HP by the specified amount. HP is clamped to [0, max]. "Set to Max" restores HP to maximum value.
- **Temporary HP Section**: A health group with header "Temporary HP" and controls.
- **Temp HP Display**: Number showing temporary hit points. Styled in blue to differentiate. Behavior: Temp HP absorbs damage before reducing current HP, doesn't stack (only highest value applies).
- **Temp HP Buttons**: Buttons labeled "+1 Temp", "+5 Temp", "Clear Temp". Behavior: Adds temporary HP or clears it. Temp HP doesn't add to max HP.
- **Hint Text**: Small gray italicized text below buttons: "Use these buttons to apply damage or healing quickly. Hit points are clamped between 0 and your maximum."
- **Hit Dice Section**: A health group with header "Hit Dice", pip display, and controls.
- **Hit Dice Pips**: Visual representation as filled/empty circles showing available vs. spent hit dice. Each pip is a small circle, filled pips in green, empty in gray. Behavior: Visually tracks hit dice usage.
- **Hit Dice Label**: Text showing die type and fraction (e.g., "1d8 (3 / 8)"). Behavior: Updates as hit dice are spent/recovered.
- **Hit Dice Buttons**: Buttons labeled "Spend 1", "Recover 1", "Refill to Level". Behavior: Adjusts available hit dice count, clamped between 0 and character level. "Refill to Level" restores all hit dice (used after long rest).
- **Hint Text**: Small gray italicized text: "Track hit dice spent during short rests. Values are limited between 0 and your character level."
- **Armor Proficiencies Section**: Header "Armor Proficiencies" with a table below showing proficient armor types as checkboxes or chips. Styled as a grid of small items.
- **Weapon Proficiencies Section**: Header "Weapon Proficiencies" with a table below showing proficient weapon types. Styled similarly to armor proficiencies.

### Spells Tab

The Spells tab provides spell management through two cards: a searchable spell library on the left and the character's prepared spellbook with spell slot tracking on the right.

#### Card 1: Spell Library

This card presents a searchable database of spells from the Open5e API. Similar in layout to the Equipment Library.

**Graphical Elements:**
- **Search Input**: Text input with placeholder "Search spells...". Styled with standard input appearance and padding. Behavior: Real-time search that filters spell list, queries Open5e API.
- **Level Filter Buttons**: A row of pill-shaped buttons labeled "All", "Cantrip", "1st", "2nd", ..., "9th". Active filter highlighted in blue. Behavior: Filters spell results to show only selected level.
- **School Filter Dropdown**: A select element with spell schools (Abjuration, Conjuration, Divination, Enchantment, Evocation, Illusion, Necromancy, Transmutation). Behavior: Further filters results by school.
- **Spell Results List**: Scrollable div containing spell cards. Each card shows: spell name (bold header), level and school (small gray text), casting time, range, components (V/S/M icons), duration, and short description. Styled with white background, border, padding, hover effect.
- **Prepare Button**: A button on each spell card labeled "Prepare" or "Learn" depending on class. Styled as primary action button with blue background. Behavior: Adds spell to prepared spells list or spellbook, checks against preparation limits.
- **Loading Indicator**: Shown during API requests. Behavior: Appears during fetch, disappears when results load.

#### Card 2: Prepared Spellbook & Spell Slots

This card shows prepared spells organized by level, with spell slot trackers for each level above cantrip.

**Graphical Elements:**
- **Spell Slots Tracker**: A grid showing spell levels 1-9 (if available based on character level) with slot tracking for each.
- **Slot Level Header**: Bold text showing spell level (e.g., "1st Level Spells", "2nd Level Spells"). Styled with bottom border.
- **Slot Pips**: Visual representation of spell slots as circles. Filled circles (green) indicate available slots, empty circles (gray) indicate used slots. Behavior: Click a filled pip to mark it as used, click an empty pip to mark it as available.
- **Slot Count Display**: Text showing "X / Y" (e.g., "2 / 4" meaning 2 used, 4 total). Appears next to pips. Behavior: Updates as pips are clicked.
- **Long Rest Button**: A prominent button below slot trackers labeled "Long Rest" or "Restore All Slots". Styled with green background. Behavior: Resets all spell slots to available (full), simulates taking a long rest.
- **Prepared Spells List**: A list of prepared spells organized by level, each spell shown as a card with name, description, and "Cast" or "Unprepare" buttons.
- **Spell Card**: Contains spell name (bold header), level and school (small text), full description, casting time, range, components, duration. Styled with light background and border.
- **Cast Button**: Button labeled "Cast" on each spell. Styled as primary action. Behavior: If the spell uses a slot, reduces available slots by 1. Shows warning if no slots remaining. Cantrips have no Cast button or unlimited casts.
- **Unprepare Button**: Small outline button labeled "Unprepare". Behavior: Removes spell from prepared list, freeing up a preparation slot.
- **Preparation Counter**: Text at top showing "X / Y spells prepared" (e.g., "8 / 12"). Behavior: Updates as spells are prepared/unprepared, limit based on class and ability modifier.

### Feats Tab

The Feats tab displays character features, feats, and custom abilities in two cards.

#### Card 1: Class Features

This card lists all class features gained from the character's selected class and level. Features are displayed as expandable items.

**Graphical Elements:**
- **Feature List**: A vertical list of class features. Each feature is a collapsible section.
- **Feature Header**: Bold text showing feature name with a small expand/collapse icon (▼/▶). Styled with subtle background and border. Behavior: Click to expand/collapse the feature description.
- **Feature Level**: Small gray text showing at which level the feature is gained (e.g., "Level 5"). Appears next to feature name.
- **Feature Description**: Collapsible text block with full feature description. Styled with padding and slightly indented. Behavior: Expands when header is clicked, showing full rules text and mechanics.
- **Empty State**: If no class selected or no features available at current level, shows message "No class features available. Select a class on the Overview tab." Styled in gray italic text.

#### Card 2: Feats & Custom Abilities

This card allows players to add and track feats and custom abilities. Feats are typically gained at certain levels or through campaign rewards.

**Graphical Elements:**
- **Add Feat Button**: A prominent button labeled "+ Add Feat" at the top of the card. Styled as primary action button with blue background. Behavior: Opens a modal or inline form to add a new feat with name and description fields.
- **Feat List**: A vertical list of feats. Each feat displayed as a card with name, description, and action buttons.
- **Feat Card**: Contains feat name (bold header), full description (text block), and edit/delete buttons. Styled with light background, border, and padding.
- **Feat Name**: Bold text showing feat name. Behavior: Click to edit (optional).
- **Feat Description**: Multi-line text showing feat effects and mechanics. Behavior: Rendered as plain text or markdown.
- **Edit Button**: Small outline button with pencil icon or "Edit" text. Behavior: Opens edit modal to modify feat name and description.
- **Delete Button**: Small red button with trash icon or "Delete" text. Behavior: Removes feat from list after confirmation.
- **Custom Abilities Section**: Similar to feats, but for campaign-specific or homebrew abilities.
- **Add Custom Ability Button**: Button labeled "+ Add Custom Ability". Behavior: Opens form to add custom ability.
- **Empty State**: If no feats or custom abilities added, shows message "No feats or custom abilities added. Click the button above to add your first one." Styled in gray italic text.

### Manage Tab

The Manage tab provides character lifecycle management, including character switching, rest mechanics, and data import/export.

#### Card 1: Character Management & Data Operations

This single card contains all management functions organized into sections.

**Section 1: Character Switcher**

**Graphical Elements:**
- **Save/Load Section Header**: Bold text "Character Management" with subtle bottom border.
- **Current Character Display**: Text showing "Current Character: [Character Name]" with character name in bold. Behavior: Updates when switching characters.
- **Character Dropdown**: A select element listing all saved characters from localStorage. Shows character names with level (e.g., "Enwer (Level 8)", "Theron (Level 3)"). Behavior: Selecting a character loads its data, replacing current sheet.
- **New Character Button**: Button labeled "Create New Character". Styled as primary action button. Behavior: Clears current sheet to defaults, prompts for new character name.
- **Delete Character Button**: Button labeled "Delete Current Character". Styled as danger button with red background. Behavior: Removes current character from localStorage after confirmation, switches to another character or blank sheet.

**Section 2: Rest Mechanics**

**Graphical Elements:**
- **Rest Section Header**: Bold text "Rest" with subtle bottom border.
- **Short Rest Button**: Large button labeled "Take Short Rest". Styled with blue background. Behavior: Allows spending hit dice to recover HP, recharges some class features. Opens a modal or inline control to spend hit dice.
- **Long Rest Button**: Large button labeled "Take Long Rest". Styled with green background. Behavior: Restores all HP to maximum, restores all hit dice to character level, restores all spell slots, recharges all abilities. Shows confirmation dialog before executing.
- **Rest Description**: Small gray text explaining rest mechanics: "Short Rest: Spend hit dice to recover HP. Long Rest: Restore all HP, hit dice, and spell slots."

**Section 3: Data Management**

**Graphical Elements:**
- **Data Section Header**: Bold text "Import / Export" with subtle bottom border.
- **Export Character Button**: Button labeled "Export Character JSON". Styled as outline button. Behavior: Generates a JSON file containing all character data, downloads file with filename format "[CharacterName]_[Class]_lvl[Level]_[Timestamp].json".
- **Export Success Message**: Temporary green message appearing after export: "Character exported successfully!" Behavior: Fades out after 3 seconds.
- **Import Character Button**: Button labeled "Import Character JSON". Styled as outline button. Behavior: Opens file picker to select a .json file, loads character data from file, replaces current sheet.
- **File Input**: Hidden file input element (styled with display: none) triggered by Import button. Accepts only .json files.
- **Import Error Message**: Temporary red message if import fails: "Error importing character. Please check the file format." Behavior: Appears on error, fades out after 5 seconds.
- **Autosave Indicator**: Small text showing last autosave timestamp (e.g., "Last saved: 2 minutes ago"). Styled in gray. Behavior: Updates every minute, shows "Saving..." during active save operations.
- **Manual Save Button**: Button labeled "Save Now". Styled as outline button. Behavior: Triggers immediate save to localStorage, updates autosave indicator.

## Testing

### Test Coverage
- Armor categorization (25 tests)
- Armor/Shield AC calculations (15 tests)
- Armor persistence
- Character AC in combat scenarios
- Equipment import/export

### Running Tests
```bash
pytest tests/test_armor_weapon_categorization.py -v
pytest tests/test_armor_shield_ac.py -v
pytest tests/ -v  # Run all tests
```

## File Structure

```
/
├── README.md                          # Main documentation
├── specifications.md                  # This file
├── requirements.txt                   # Python dependencies
├── config.json                        # Configuration
├── backend.py                         # Python backend server
├── static/
│   ├── index.html                    # Main character sheet UI
│   └── assets/
│       ├── py/                       # Python modules (Pyodide)
│       │   ├── character.py          # Character system core
│       │   ├── armor_manager.py      # Armor calculations
│       │   ├── equipment_management.py # Equipment UI/logic
│       │   ├── equipment_data.py     # Equipment database
│       │   └── ...
│       ├── css/
│       └── js/
├── docs/                              # Additional documentation
├── tests/                             # Test suite
├── exports/                           # Character exports
│   └── autosaves/                    # Autosaved characters
└── tools/                             # Utility scripts
```

## Version History

- **Current:** 1.0.0
- **Started:** January 2026
- **Last Updated:** January 25, 2026

## Future Enhancements

- [ ] Spell system with spell slots
- [ ] Multi-class support
- [ ] Feats system
- [ ] Ability score improvements tracking
- [ ] Condition system
- [ ] Party management
- [ ] Campaign notes
- [ ] Mobile optimizations

## Contact/Support

For issues, bugs, or feature requests, refer to the project documentation in `/docs/`.
