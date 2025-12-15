"""Equipment management module for PySheet D&D 5e character app.

Contains inventory management, equipment rendering, and class features/domains database.
"""

import json
import re
from typing import Union, Optional
from html import escape

# Import Entity from same package
try:
    from entities import Entity
except ImportError:
    # For testing/non-PyScript environments, define a minimal Entity
    class Entity:
        def __init__(self, name: str, entity_type: str = "", description: str = ""):
            self.name = name
            self.entity_type = entity_type
            self.description = description
            self.properties = {}

# =============================================================================
# PyScript/Pyodide Imports with Guards
# =============================================================================

try:
    from js import console, document, window
except ImportError:
    # Mock for testing environments
    class _MockConsole:
        @staticmethod
        def log(*args): pass
        @staticmethod
        def warn(*args): pass
        @staticmethod
        def error(*args): pass
    
    console = _MockConsole()
    document = None
    window = None

try:
    from pyodide.ffi import create_proxy
except ImportError:
    # Mock for testing
    def create_proxy(func):
        return func

# =============================================================================
# Global State & Event Tracking
# =============================================================================

_EVENT_PROXIES = []
EQUIPMENT_LIBRARY_STATE = {}
WEAPON_LIBRARY_STATE = {"weapons": [], "weapon_map": {}, "loading": False, "loaded": False}

# Module references captured at load time to avoid proxy lifecycle issues
# These are set during module initialization and stay alive throughout
# NOTE: We store MODULE references, not function references, to avoid PyScript proxy lifecycle issues
_CHAR_MODULE_REF = None
_EXPORT_MODULE_REF = None

# =============================================================================
# Armor Data & Classifications
# =============================================================================

ARMOR_TYPES = {
    "light": ["leather", "studded leather", "studded"],
    "medium": ["hide", "chain shirt", "scale mail", "breastplate", "half plate"],
    "heavy": ["plate", "chain mail", "splint", "splint armor"],
}

# D&D 5e standard armor AC values (from PHB)
ARMOR_AC_VALUES = {
    "leather": 11,
    "studded leather": 12,
    "studded": 12,
    "hide": 12,
    "chain shirt": 13,
    "scale mail": 14,
    "breastplate": 14,
    "half plate": 15,
    "plate": 18,
    "chain mail": 16,
    "splint": 17,
    "splint armor": 17,
}

# =============================================================================
# Armor Utility Functions
# =============================================================================

def get_armor_type(armor_name: str) -> str:
    """Determine armor type (light, medium, heavy) from armor name."""
    name_lower = armor_name.lower()
    for armor_type, names in ARMOR_TYPES.items():
        for name_pattern in names:
            if name_pattern in name_lower:
                return armor_type
    return "unknown"


def get_armor_ac(armor_name: str) -> int:
    """Get standard D&D 5e AC value for armor by name. Returns None if not standard armor."""
    name_lower = armor_name.lower()
    for armor_pattern, ac_value in ARMOR_AC_VALUES.items():
        if armor_pattern in name_lower:
            return ac_value
    return None

# =============================================================================
# Format Utility Functions
# =============================================================================

def format_money(value: float) -> str:
    """Format a numeric value as currency."""
    try:
        return f"{value:.2f}"
    except Exception:
        return str(value)


def format_weight(value: float) -> str:
    """Format a numeric value as weight."""
    try:
        return f"{value:.2f}"
    except Exception:
        return str(value)

# =============================================================================
# DOM Utility Functions (Stubs for PyScript Integration)
# =============================================================================

def get_element(element_id: str):
    """Get DOM element by ID."""
    if document is None:
        return None
    try:
        return document.getElementById(element_id)
    except:
        return None


def get_text_value(element_id: str) -> str:
    """Get text value from element."""
    el = get_element(element_id)
    if el is None:
        return ""
    return el.value if hasattr(el, 'value') else (el.textContent or "")


def get_numeric_value(element_id: str, default: int = 0) -> int:
    """Get numeric value from element."""
    try:
        return int(get_text_value(element_id))
    except (ValueError, TypeError):
        return default


def get_checkbox(element_id: str) -> bool:
    """Get checkbox state from element."""
    el = get_element(element_id)
    if el is None:
        return False
    return el.checked if hasattr(el, 'checked') else False


def set_text(element_id: str, value: str):
    """Set text content of element."""
    el = get_element(element_id)
    if el is not None:
        if hasattr(el, 'textContent'):
            el.textContent = str(value)
        elif hasattr(el, 'value'):
            el.value = str(value)


def ability_modifier(score: int) -> int:
    """Calculate ability modifier from ability score."""
    return (score - 10) // 2


def format_bonus(value: int) -> str:
    """Format a modifier as +X or -X."""
    if value > 0:
        return f"+{value}"
    return str(value)


def parse_int(value, default: int = 0) -> int:
    """Parse a value as integer with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    import uuid
    return f"{prefix}_{str(uuid.uuid4())[:8]}"

# =============================================================================
# Item Classes
# =============================================================================

class Item(Entity):
    """Base class for all inventory items - inherits from Entity for unified object model."""
    
    def __init__(self, name: str, cost: str = "", weight: str = "", qty: int = 1, category: str = "", notes: str = "", source: str = "custom"):
        """Initialize an Item.
        
        Args:
            name: Item name
            cost: Cost in gold/silver/copper (e.g., "5 gp", "10 sp")
            weight: Weight (e.g., "4 lb.", "0 lb.")
            qty: Quantity
            category: Item category (Armor, Weapons, etc.)
            notes: JSON string of extra properties
            source: Source of item (custom, open5e, phb, etc.)
        """
        super().__init__(name, entity_type="item", description="")
        self.cost = cost
        self.weight = weight
        self.qty = qty
        self.category = category
        self.notes = notes
        self.source = source
        self.id = str(len([]))  # Will be set by InventoryManager
    
    def to_dict(self) -> dict:
        """Convert item to dictionary for storage."""
        d = super().to_dict()
        d.update({
            "id": self.id,
            "cost": self.cost,
            "weight": self.weight,
            "qty": self.qty,
            "category": self.category,
            "notes": self.notes,
            "source": self.source,
        })
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Create item from dictionary."""
        return cls(
            name=data.get("name", ""),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            qty=data.get("qty", 1),
            category=data.get("category", ""),
            notes=data.get("notes", ""),
            source=data.get("source", "custom"),
        )


class Weapon(Item):
    """Weapon item with damage and properties."""
    
    def __init__(self, name: str, cost: str = "", weight: str = "", qty: int = 1, category: str = "Weapons", 
                 notes: str = "", source: str = "custom", damage: str = "", damage_type: str = "", 
                 range_text: str = "", properties: str = ""):
        super().__init__(name, cost, weight, qty, category, notes, source)
        self.damage = damage
        self.damage_type = damage_type
        self.range_text = range_text
        self.weapon_properties = properties  # Changed from self.properties to avoid conflict with Entity.properties
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        extra_props = {}
        if self.damage:
            extra_props["damage"] = self.damage
        if self.damage_type:
            extra_props["damage_type"] = self.damage_type
        if self.range_text:
            extra_props["range"] = self.range_text
        if self.weapon_properties:
            extra_props["properties"] = self.weapon_properties
        if extra_props:
            d["notes"] = json.dumps(extra_props) if not d["notes"] else d["notes"]
        return d


class Armor(Item):
    """Armor item with AC value."""
    
    def __init__(self, name: str, cost: str = "", weight: str = "", qty: int = 1, 
                 notes: str = "", source: str = "custom", armor_class: int = None):
        super().__init__(name, cost, weight, qty, "Armor", notes, source)
        self.armor_class = armor_class
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.armor_class:
            extra_props = {}
            try:
                if d.get("notes"):
                    extra_props = json.loads(d["notes"])
            except:
                pass
            extra_props["armor_class"] = self.armor_class
            d["notes"] = json.dumps(extra_props)
        return d


class Shield(Item):
    """Shield item with AC bonus."""
    
    def __init__(self, name: str, cost: str = "", weight: str = "", qty: int = 1,
                 notes: str = "", source: str = "custom", ac_bonus: str = "+2"):
        super().__init__(name, cost, weight, qty, "Armor", notes, source)
        self.ac_bonus = ac_bonus
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.ac_bonus:
            extra_props = {}
            try:
                if d.get("notes"):
                    extra_props = json.loads(d["notes"])
            except:
                pass
            extra_props["ac_bonus"] = self.ac_bonus
            d["notes"] = json.dumps(extra_props)
        return d


class Equipment(Item):
    """Generic equipment/gear item."""
    
    def __init__(self, name: str, cost: str = "", weight: str = "", qty: int = 1,
                 category: str = "Adventuring Gear", notes: str = "", source: str = "custom"):
        super().__init__(name, cost, weight, qty, category, notes, source)

# =============================================================================
# InventoryManager Class (650 lines)
# =============================================================================

class InventoryManager:
    """Manages character inventory with categories, sorting, and detailed item view."""
    
    # Common item categories for auto-detection
    ARMOR_KEYWORDS = ["armor", "plate", "mail", "leather", "chain", "scale", "shield", "helmet", "breastplate"]
    WEAPON_KEYWORDS = ["sword", "axe", "spear", "bow", "staff", "mace", "hammer", "dagger", "knife", "blade", "rapier", "wand"]
    AMMO_KEYWORDS = ["arrow", "bolt", "ammo", "ammunition", "shot"]
    TOOL_KEYWORDS = ["tool", "kit", "instrument", "lock pick", "thieves'", "healer's"]
    POTION_KEYWORDS = ["potion", "elixir", "oil", "poison", "cure", "healing"]
    GEAR_KEYWORDS = ["rope", "torch", "bedroll", "tent", "lantern", "backpack", "grappling hook", "caltrops", "chalk", "pack", "explorer", "adventurer", "burglar", "diplomat", "dungeoneer", "entertainer", "priest", "scholar"]
    MOUNT_KEYWORDS = ["horse", "mule", "donkey", "camel", "mount", "vehicle", "cart", "boat", "ship"]
    MAGIC_KEYWORDS = ["+1", "+2", "+3", "magical", "magic", "enchanted", "ring of", "cloak of", "amulet of", "wand of", "staff of", "artifact", "relic"]
    
    # Category ordering for display
    CATEGORY_ORDER = ["Magic Items", "Weapons", "Armor", "Ammunition", "Potions", "Tools", "Adventuring Gear", "Mounts & Vehicles", "Other"]
    
    def __init__(self):
        self.items: list[dict] = []
    
    def load_state(self, state: Optional[dict]):
        """Load inventory from character state."""
        if not state:
            self.items = []
            return
        
        # Try to get items from inventory.items (new format)
        inventory = state.get("inventory", {})
        items_list = inventory.get("items", [])
        
        # Fallback to equipment for backward compatibility
        if not items_list:
            items_list = state.get("equipment", [])
        
        self.items = []
        for item in items_list:
            if isinstance(item, dict):
                # Ensure all required fields exist
                if "id" not in item:
                    item["id"] = str(len(self.items))
                if "category" not in item:
                    item["category"] = self._infer_category(item.get("name", ""))
                if "qty" not in item:
                    item["qty"] = item.get("quantity", 1)
                self.items.append(item)
    
    def _infer_category(self, name: str) -> str:
        """Auto-detect item category from name."""
        name_lower = name.lower()
        # Check for magic items first (they might contain weapon/armor keywords too)
        if any(keyword in name_lower for keyword in self.MAGIC_KEYWORDS):
            return "Magic Items"
        elif any(keyword in name_lower for keyword in self.ARMOR_KEYWORDS):
            return "Armor"
        elif any(keyword in name_lower for keyword in self.WEAPON_KEYWORDS):
            return "Weapons"
        elif any(keyword in name_lower for keyword in self.AMMO_KEYWORDS):
            return "Ammunition"
        elif any(keyword in name_lower for keyword in self.TOOL_KEYWORDS):
            return "Tools"
        elif any(keyword in name_lower for keyword in self.POTION_KEYWORDS):
            return "Potions"
        elif any(keyword in name_lower for keyword in self.GEAR_KEYWORDS):
            return "Adventuring Gear"
        elif any(keyword in name_lower for keyword in self.MOUNT_KEYWORDS):
            return "Mounts & Vehicles"
        return "Other"
    
    def add_item(self, name: str, cost: str = "", weight: str = "", qty: int = 1, 
                 category: str = "", notes: str = "", source: str = "custom") -> str:
        """Add an item to inventory and return its ID."""
        item_id = str(len(self.items))
        if not category:
            category = self._infer_category(name)
        
        item = {
            "id": item_id,
            "name": name,
            "cost": cost,
            "weight": weight,
            "qty": qty,
            "category": category,
            "notes": notes,
            "source": source,
            "equipped": False,
        }
        self.items.append(item)
        return item_id
    
    def remove_item(self, item_id: str):
        """Remove an item by ID."""
        self.items = [item for item in self.items if item.get("id") != item_id]
    
    def get_item(self, item_id: str) -> Optional[dict]:
        """Get an item by ID."""
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None
    
    def update_item(self, item_id: str, updates: dict):
        """Update item fields."""
        for item in self.items:
            if item.get("id") == item_id:
                for key, value in updates.items():
                    if key in ("name", "cost", "weight", "qty", "category", "notes", "equipped"):
                        item[key] = value
                break
    
    def get_items_by_category(self) -> dict[str, list[dict]]:
        """Group items by category, sorted within each category."""
        grouped = {}
        for item in self.items:
            category = item.get("category", "Other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(item)
        
        # Sort items within each category alphabetically
        for category in grouped:
            grouped[category].sort(key=lambda x: x.get("name", "").lower())
        
        # Return in defined order, putting unlisted categories at end
        result = {}
        for category in self.CATEGORY_ORDER:
            if category in grouped:
                result[category] = grouped[category]
        for category in sorted(grouped.keys()):
            if category not in result:
                result[category] = grouped[category]
        
        return result
    
    def get_total_weight(self) -> float:
        """Calculate total weight of items."""
        total = 0.0
        for item in self.items:
            weight_str = item.get("weight", "").strip().lower()
            qty = item.get("qty", 1)
            if weight_str:
                # Extract number from strings like "2 lb", "0.5 lb", "2lb"
                match = re.search(r'(\d+\.?\d*)', weight_str)
                if match:
                    try:
                        total += float(match.group(1)) * qty
                    except:
                        pass
        return total
    
    def render_inventory(self):
        """Render inventory list with categories and expandable items."""
        container = get_element("inventory-list")
        if container is None:
            return
        
        items_grouped = self.get_items_by_category()
        sections_html = []
        
        if not self.items:
            container.innerHTML = ""
            empty_msg = get_element("inventory-empty-state")
            if empty_msg:
                empty_msg.style.display = "block"
            return
        
        empty_msg = get_element("inventory-empty-state")
        if empty_msg:
            empty_msg.style.display = "none"
        
        # Build HTML for each category
        for category, items in items_grouped.items():
            category_html = f'<div class="inventory-category">'
            category_html += f'<div class="inventory-category-header">{escape(category)}</div>'
            
            # Add items in this category
            for item in items:
                item_id = item.get("id", "")
                name = item.get("name", "Unknown Item")
                qty = item.get("qty", 1)
                cost = item.get("cost", "")
                weight = item.get("weight", "")
                notes = item.get("notes", "")
                
                # Parse extra properties from notes JSON if present
                extra_props = {}
                try:
                    if notes and notes.startswith("{"):
                        extra_props = json.loads(notes)
                        notes = ""  # Clear notes since we're using it for storage
                except:
                    pass
                
                # Get bonus for weapons and armor
                bonus = extra_props.get("bonus", 0)
                display_name = name
                if bonus and bonus != 0:
                    bonus_str = f"+{bonus}" if bonus > 0 else str(bonus)
                    display_name = f"{name} {bonus_str}"
                
                # Build cost/weight display
                details_html = ""
                if cost:
                    details_html += f'<span class="inventory-item-cost"><strong>Cost:</strong> {escape(str(cost))}</span>'
                if weight:
                    details_html += f'<span class="inventory-item-weight"><strong>Weight:</strong> {escape(str(weight))}</span>'
                
                # Build body content with expandable properties
                body_html = ''
                
                # Show weapon/armor properties if available
                if extra_props.get("damage"):
                    body_html += f'<div class="inventory-item-field"><label>Damage</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("damage")))}</div></div>'
                if extra_props.get("damage_type"):
                    body_html += f'<div class="inventory-item-field"><label>Damage Type</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("damage_type")))}</div></div>'
                if extra_props.get("range"):
                    body_html += f'<div class="inventory-item-field"><label>Range</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("range")))}</div></div>'
                if extra_props.get("properties"):
                    body_html += f'<div class="inventory-item-field"><label>Properties/Contents</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("properties")))}</div></div>'
                
                # For armor items, show ONLY editable AC field
                if category == "Armor":
                    ac_val = extra_props.get("armor_class", "")
                    body_html += f'<div class="inventory-item-field"><label>AC</label><input type="number" data-item-armor-ac="{item_id}" value="{ac_val}" placeholder="Base AC" style="width: 100%;"></div>'
                    # Add bonus spinner for armor
                    bonus_val = extra_props.get("bonus", 0)
                    body_html += f'<div class="inventory-item-field"><label>Bonus</label><input type="number" data-item-bonus="{item_id}" value="{bonus_val}" placeholder="0" style="width: 80px;"></div>'
                
                # For weapon items, add bonus spinner
                if category == "Weapons":
                    bonus_val = extra_props.get("bonus", 0)
                    body_html += f'<div class="inventory-item-field"><label>Bonus</label><input type="number" data-item-bonus="{item_id}" value="{bonus_val}" placeholder="0" style="width: 80px;"></div>'
                
                # Show notes if present (after we cleared it for prop parsing)
                if notes:
                    body_html += f'<div class="inventory-item-field"><label>Notes</label><div style="color: #bfdbfe;">{escape(notes)}</div></div>'
                
                # Special handling for Magic Items being imported
                if name == "Unnamed Magic Item":
                    body_html += f'<div class="inventory-item-field" style="background-color: #1e293b; padding: 12px; border-radius: 4px; border: 2px solid #3b82f6;">'
                    body_html += f'<label style="color: #60a5fa;"><strong>📡 Import Magic Item from URL</strong></label>'
                    body_html += f'<input id="magic-item-url-{item_id}" type="text" placeholder="https://roll20.net/compendium/..." style="width: 100%; padding: 8px; margin-top: 8px; font-family: monospace; font-size: 0.9em; border: 1px solid #475569; border-radius: 4px; background-color: #0f172a; color: #e2e8f0;">'
                    body_html += f'<button id="magic-item-fetch-{item_id}" type="button" style="width: 100%; padding: 8px; margin-top: 8px; background-color: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">Fetch Data</button>'
                    body_html += f'</div>'
                
                # Quantity field - useful for all items
                body_html += f'<div class="inventory-item-field"><label>Quantity</label><input type="number" min="1" value="{qty}" data-item-qty="{item_id}" style="width: 80px;"></div>'
                
                # Build category dropdown with current category selected
                category_options = [
                    ("Magic Items", "Magic Items"),
                    ("Weapons", "Weapons"),
                    ("Armor", "Armor"),
                    ("Ammunition", "Ammunition"),
                    ("Potions", "Potions"),
                    ("Tools", "Tools"),
                    ("Adventuring Gear", "Adventuring Gear"),
                    ("Mounts & Vehicles", "Mounts & Vehicles"),
                    ("Other", "Other")
                ]
                category_select_html = f'<select data-item-category="{item_id}" style="width: 100%;">'
                for cat_value, cat_label in category_options:
                    selected = "selected" if cat_value == item.get("category", "Other") else ""
                    category_select_html += f'<option value="{cat_value}" {selected}>{cat_label}</option>'
                category_select_html += '</select>'
                body_html += f'<div class="inventory-item-field"><label>Category</label>{category_select_html}</div>'
                
                # Determine if item is equipable (armor or weapon)
                is_armor = category in ["Armor", "Weapons"]
                is_weapon = category == "Weapons"
                equipable = is_armor
                equipped_checked = "checked" if item.get("equipped") else ""
                equipped_decorator = "⭐ " if item.get("equipped") else ""
                
                # DEBUG: Log which item is being marked as equipped
                if equipped_decorator:
                    console.log(f"[DEBUG] Rendering equipped item: id={item_id}, name={name}, category={category}")
                
                # Add equipped checkbox to body_html (visible only when details expanded)
                if equipable:
                    body_html += f'<div class="inventory-item-field"><label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; user-select: none;"><input type="checkbox" data-item-equipped="{item_id}" {equipped_checked} class="equipment-equipped-check" style="cursor: pointer;"><span>Equipped</span></label></div>'
                
                category_html += f'''<li class="inventory-item" data-item-id="{escape(item_id)}">
                    <div class="inventory-item-summary" data-toggle-item="{escape(item_id)}">
                        <div class="inventory-item-main">
                            <span class="inventory-item-name">{equipped_decorator}{escape(display_name)}</span>
                            <span class="inventory-item-qty">×{qty}</span>
                        </div>
                        <div class="inventory-item-details">
                            {details_html}
                        </div>
                        <div class="inventory-item-actions">
                            <button class="inventory-item-remove" data-remove-item="{escape(item_id)}" type="button">Remove</button>
                        </div>
                    </div>
                    <div class="inventory-item-body" data-item-body="{escape(item_id)}">
                        {body_html}
                    </div>
                </li>'''
            
            category_html += '</div>'
            sections_html.append(category_html)
        
        container.innerHTML = "".join(sections_html)
        
        # Register event handlers
        self._register_item_handlers()
        
        # Update totals
        update_inventory_totals()
    
    def _register_item_handlers(self):
        """Register click handlers for inventory items."""
        if document is None:
            return
        
        # Toggle expand/collapse
        inventory_list = get_element("inventory-list")
        if inventory_list is None:
            return
        
        toggles = inventory_list.querySelectorAll("[data-toggle-item]")
        for toggle in toggles:
            item_id = toggle.getAttribute("data-toggle-item")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_item_toggle(event, iid))
            toggle.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Remove buttons
        removes = inventory_list.querySelectorAll("[data-remove-item]")
        for remove_btn in removes:
            item_id = remove_btn.getAttribute("data-remove-item")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_item_remove(event, iid))
            remove_btn.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Qty changes
        qty_inputs = inventory_list.querySelectorAll("[data-item-qty]")
        for qty_input in qty_inputs:
            item_id = qty_input.getAttribute("data-item-qty")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_qty_change(event, iid))
            qty_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Category changes
        cat_selects = inventory_list.querySelectorAll("[data-item-category]")
        for cat_select in cat_selects:
            item_id = cat_select.getAttribute("data-item-category")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_category_change(event, iid))
            cat_select.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Custom properties changes
        custom_props_inputs = inventory_list.querySelectorAll("[data-item-custom-props]")
        for props_input in custom_props_inputs:
            item_id = props_input.getAttribute("data-item-custom-props")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_custom_props_change(event, iid))
            props_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # AC modifier changes
        ac_mod_inputs = inventory_list.querySelectorAll("[data-item-ac-mod]")
        for ac_input in ac_mod_inputs:
            item_id = ac_input.getAttribute("data-item-ac-mod")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_modifier_change(event, iid, "ac_modifier"))
            ac_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Saves modifier changes
        saves_mod_inputs = inventory_list.querySelectorAll("[data-item-saves-mod]")
        for saves_input in saves_mod_inputs:
            item_id = saves_input.getAttribute("data-item-saves-mod")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_modifier_change(event, iid, "saves_modifier"))
            saves_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Armor-only checkbox changes
        armor_only_checkboxes = inventory_list.querySelectorAll("[data-item-armor-only]")
        for checkbox in armor_only_checkboxes:
            item_id = checkbox.getAttribute("data-item-armor-only")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_armor_only_toggle(event, iid))
            checkbox.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Armor AC value changes
        armor_ac_inputs = inventory_list.querySelectorAll("[data-item-armor-ac]")
        for ac_input in armor_ac_inputs:
            item_id = ac_input.getAttribute("data-item-armor-ac")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_armor_ac_change(event, iid))
            ac_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Bonus value changes (for weapons and armor)
        bonus_inputs = inventory_list.querySelectorAll("[data-item-bonus]")
        for bonus_input in bonus_inputs:
            item_id = bonus_input.getAttribute("data-item-bonus")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_bonus_change(event, iid))
            bonus_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Equipped checkboxes
        equipped_checkboxes = inventory_list.querySelectorAll("[data-item-equipped]")
        for checkbox in equipped_checkboxes:
            item_id = checkbox.getAttribute("data-item-equipped")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_equipped_toggle(event, iid))
            checkbox.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Magic Item fetch buttons
        fetch_buttons = inventory_list.querySelectorAll("button[id^='magic-item-fetch-']")
        for btn in fetch_buttons:
            btn_id = btn.getAttribute("id")
            item_id = btn_id.replace("magic-item-fetch-", "")
            def make_fetch_handler(iid):
                def handle_fetch(event):
                    url_input = document.getElementById(f"magic-item-url-{iid}")
                    if url_input:
                        url = url_input.value.strip()
                        if url:
                            console.log(f"PySheet: Fetching magic item from {url}")
                            self._fetch_magic_item(iid, url)
                return handle_fetch
            proxy = create_proxy(make_fetch_handler(item_id))
            btn.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _handle_item_toggle(self, event, item_id: str):
        """Toggle item details visibility."""
        console.log(f"[DEBUG] _handle_item_toggle called with item_id={item_id}")
        if document is None:
            return
        body = document.querySelector(f"[data-item-body='{item_id}']")
        console.log(f"[DEBUG] Looking for body with data-item-body='{item_id}', found: {body is not None}")
        if body:
            if body.classList.contains("open"):
                body.classList.remove("open")
                console.log(f"[DEBUG] Closed item {item_id}")
            else:
                body.classList.add("open")
                console.log(f"[DEBUG] Opened item {item_id}")
        else:
            console.error(f"[ERROR] Could not find body element for item {item_id}")
    
    def _handle_item_remove(self, event, item_id: str):
        """Remove an item."""
        console.log(f"[REMOVE] _handle_item_remove called for item_id={item_id}")
        event.stopPropagation()
        event.preventDefault()
        self.remove_item(item_id)
        console.log(f"[REMOVE] Item removed from inventory, total items: {len(self.items)}")
        self.render_inventory()
        console.log(f"[REMOVE] Inventory re-rendered")
        update_calculations()
        console.log(f"[REMOVE] Calculations updated")
        
        # Ensure module references are initialized
        initialize_module_references()
        console.log(f"[REMOVE] Module references initialized, _CHAR_MODULE_REF={_CHAR_MODULE_REF is not None}")
        
        # Re-render weapons grid in case the removed item was a weapon
        if _CHAR_MODULE_REF is not None:
            console.log(f"[REMOVE] _CHAR_MODULE_REF is available, checking for render_equipped_weapons")
            if hasattr(_CHAR_MODULE_REF, 'render_equipped_weapons'):
                try:
                    console.log(f"[REMOVE] Calling render_equipped_weapons()")
                    _CHAR_MODULE_REF.render_equipped_weapons()
                    console.log(f"[REMOVE] Successfully called render_equipped_weapons()")
                except Exception as e:
                    console.error(f"[REMOVE] ERROR calling render_equipped_weapons(): {e}")
            else:
                console.log(f"[REMOVE] render_equipped_weapons not found in _CHAR_MODULE_REF")
        else:
            console.log(f"[REMOVE] _CHAR_MODULE_REF is None, cannot render weapons")
    def _handle_qty_change(self, event, item_id: str):
        """Handle quantity changes."""
        qty_input = event.target
        qty = parse_int(qty_input.value, 1)
        self.update_item(item_id, {"qty": qty})
        self.render_inventory()
    def _handle_category_change(self, event, item_id: str):
        """Handle category changes."""
        cat_select = event.target
        category = cat_select.value or "Other"
        self.update_item(item_id, {"category": category})
        self.render_inventory()
    def _handle_custom_props_change(self, event, item_id: str):
        """Handle custom properties/effects changes."""
        props_input = event.target
        custom_props = props_input.value.strip()
        
        # Update the item's notes field with the custom properties
        item = self.get_item(item_id)
        if item:
            try:
                # Parse existing notes to preserve other properties
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                else:
                    extra_props = {}
            except:
                extra_props = {}
            
            # Update custom properties
            extra_props["custom_properties"] = custom_props
            
            # Save back to notes
            notes = json.dumps(extra_props) if extra_props else ""
            self.update_item(item_id, {"notes": notes})
            self.render_inventory()
    def _handle_modifier_change(self, event, item_id: str, modifier_type: str):
        """Handle AC or Saves modifier changes."""
        mod_input = event.target
        mod_value_str = mod_input.value.strip()
        
        # Convert to int or keep empty
        try:
            mod_value = int(mod_value_str) if mod_value_str else ""
        except:
            mod_value = ""
        
        # Update the item's notes field with the modifier
        item = self.get_item(item_id)
        if item:
            try:
                # Parse existing notes to preserve other properties
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                else:
                    extra_props = {}
            except:
                extra_props = {}
            
            # Update modifier
            if mod_value != "":
                extra_props[modifier_type] = mod_value
            else:
                # Remove if empty
                if modifier_type in extra_props:
                    del extra_props[modifier_type]
            
            # Save back to notes
            notes = json.dumps(extra_props) if extra_props else ""
            self.update_item(item_id, {"notes": notes})
            self.render_inventory()  # Update display
            
            # Update calculations (which will recalculate AC and stats)
            update_calculations()
    def _handle_armor_only_toggle(self, event, item_id: str):
        """Handle armor-only flag toggle for magic armor/shields."""
        checkbox = event.target
        is_armor_only = checkbox.checked
        
        # Update the item's notes field with the armor_only flag
        item = self.get_item(item_id)
        if item:
            try:
                # Parse existing notes to preserve other properties
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                else:
                    extra_props = {}
            except:
                extra_props = {}
            
            # Update armor_only flag
            if is_armor_only:
                extra_props["armor_only"] = True
                # When marking as armor-only, clear saves_modifier since it shouldn't apply
                if "saves_modifier" in extra_props:
                    del extra_props["saves_modifier"]
            else:
                if "armor_only" in extra_props:
                    del extra_props["armor_only"]
            
            # Save back to notes
            notes = json.dumps(extra_props) if extra_props else ""
            self.update_item(item_id, {"notes": notes})
            self.render_inventory()  # Update display
            
            # Update calculations (which will recalculate AC and stats)
            update_calculations()
    def _handle_armor_ac_change(self, event, item_id: str):
        """Handle armor AC base value changes."""
        ac_input = event.target
        ac_val_str = ac_input.value.strip()
        
        # Parse AC value
        try:
            ac_val = int(ac_val_str) if ac_val_str else None
        except:
            ac_val = None
        
        # Update the item's notes field with the armor_class value
        item = self.get_item(item_id)
        if item:
            try:
                # Parse existing notes to preserve other properties
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                else:
                    extra_props = {}
            except:
                extra_props = {}
            
            # Update armor_class value
            if ac_val is not None:
                extra_props["armor_class"] = ac_val
            elif "armor_class" in extra_props:
                del extra_props["armor_class"]
            
            # Save back to notes
            notes = json.dumps(extra_props) if extra_props else ""
            self.update_item(item_id, {"notes": notes})
            self.render_inventory()  # Update display
            
            # Update calculations (which will recalculate AC with new armor base)
            update_calculations()
    
    def _handle_bonus_change(self, event, item_id: str):
        """Handle weapon/armor bonus changes."""
        bonus_input = event.target
        bonus_val_str = bonus_input.value.strip()
        
        # Parse bonus value
        try:
            bonus_val = int(bonus_val_str) if bonus_val_str else 0
        except:
            bonus_val = 0
        
        # Update the item's notes field with the bonus value
        item = self.get_item(item_id)
        if item:
            try:
                # Parse existing notes to preserve other properties
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                else:
                    extra_props = {}
            except:
                extra_props = {}
            
            # Update bonus value
            if bonus_val != 0:
                extra_props["bonus"] = bonus_val
            elif "bonus" in extra_props:
                del extra_props["bonus"]
            
            # Save back to notes
            notes = json.dumps(extra_props) if extra_props else ""
            self.update_item(item_id, {"notes": notes})
            self.render_inventory()  # Update display to show new name with bonus
            
            # Update calculations if needed
            update_calculations()
    
    def _handle_equipped_toggle(self, event, item_id: str):
        """Handle equipped checkbox toggle."""
        try:
            checkbox = event.target
            equipped = bool(checkbox.checked)
            
            # Update item's equipped flag
            item = self.get_item(item_id)
            if item:
                self.update_item(item_id, {"equipped": equipped})
                console.log(f"PySheet: Equipment {item.get('name')} equipped={equipped}")
                
                # Re-render inventory to update decorator
                self.render_inventory()
                
                # Ensure module references are initialized (lazy initialization for export_management)
                initialize_module_references()
                
                # Call update_calculations() through main module to avoid proxy lifecycle issues
                if _CHAR_MODULE_REF is not None and hasattr(_CHAR_MODULE_REF, 'update_calculations'):
                    try:
                        _CHAR_MODULE_REF.update_calculations()
                        console.log("DEBUG: Called update_calculations() - checkbox handler")
                    except Exception as calc_err:
                        console.error(f"ERROR in update_calculations(): {calc_err}")
                        raise  # Re-raise so the outer handler catches it
                
                # Auto-save character data through export_management module reference
                # Call directly through module to avoid PyScript proxy lifecycle issues
                if _EXPORT_MODULE_REF is not None and hasattr(_EXPORT_MODULE_REF, 'schedule_auto_export'):
                    try:
                        _EXPORT_MODULE_REF.schedule_auto_export()
                        console.log("DEBUG: Called schedule_auto_export() - checkbox handler")
                    except Exception as export_err:
                        console.error(f"ERROR in schedule_auto_export(): {export_err}")
                        # Don't re-raise here, log but continue
        except Exception as e:
            console.error(f"CRITICAL ERROR in _handle_equipped_toggle: {e}")

    
    def _fetch_magic_item(self, item_id: str, url: str):
        """Fetch magic item data from URL and update the item"""
        try:
            def on_response(response):
                if response.ok:
                    def on_text(html):
                        # Parse the HTML to extract item data
                        self._parse_magic_item_data(item_id, html)
                    response.text().then(on_text)
                else:
                    console.error(f"PySheet: Failed to fetch {url}: {response.status}")
            
            def on_error(err):
                console.error(f"PySheet: Network error: {err}")
            
            window.fetch(url).then(on_response).catch(on_error)
        except Exception as e:
            console.error(f"PySheet: Error fetching magic item: {e}")
    
    
    def _parse_magic_item_data(self, item_id: str, html: str):
        """Parse magic item data from HTML"""
        try:
            # Extract item name - look for common patterns
            name_patterns = [
                r'<h1[^>]*>([^<]+)</h1>',
                r'<h2[^>]*>([^<]+)</h2>',
                r'<strong[^>]*>([^<]*(?:of|Disruption|Health|Protection|Ward)[^<]*)</strong>',
            ]
            name = "Magic Item"
            for pattern in name_patterns:
                match = re.search(pattern, html)
                if match:
                    name = match.group(1).strip()
                    break
            
            # Extract damage (e.g., "1d6" or "2d6")
            damage = ""
            damage_match = re.search(r'[Dd]amage[:\s]*(\d+d\d+(?:\+\d+)?)', html)
            if damage_match:
                damage = damage_match.group(1)
            
            # Extract damage type
            damage_type = ""
            dtype_match = re.search(r'[Dd]amage\s+[Tt]ype[:\s]*([A-Za-z]+)', html)
            if dtype_match:
                damage_type = dtype_match.group(1)
            
            # Extract weight
            weight = "0 lb."
            weight_match = re.search(r'[Ww]eight[:\s]*([0-9.]+\s*(?:lb|lbs|kg)\.?)', html)
            if weight_match:
                weight = weight_match.group(1)
            
            # Extract rarity
            rarity = ""
            rarity_match = re.search(r'[Rr]arity[:\s]*([A-Za-z]+)', html)
            if rarity_match:
                rarity = rarity_match.group(1)
            
            # Build the updated item data
            item = self.get_item(item_id)
            if item:
                # Update name if found
                if name != "Magic Item":
                    item["name"] = name
                
                # Build notes with extracted data
                extra_props = {}
                if damage:
                    extra_props["damage"] = damage
                if damage_type:
                    extra_props["damage_type"] = damage_type
                if rarity:
                    extra_props["rarity"] = rarity
                
                item["weight"] = weight
                item["notes"] = json.dumps(extra_props) if extra_props else ""
                
                self.update_item(item_id, item)
                self.render_inventory()
                update_calculations()
                console.log(f"PySheet: Updated magic item to '{name}'")
        except Exception as e:
            console.error(f"PySheet: Error parsing magic item: {e}")


# =============================================================================
# Singleton Instance
# =============================================================================

INVENTORY_MANAGER = InventoryManager()

# =============================================================================
# Stub Functions (Placeholders - Override in character.py)
# =============================================================================

def update_calculations(*_args):
    """Update character calculations. Override in character.py."""
    pass


def schedule_auto_export():
    """Schedule auto-export. Override in character.py."""
    pass


def update_inventory_totals():
    """Update total weight and cost displays."""
    total_weight = INVENTORY_MANAGER.get_total_weight()
    weight_el = get_element("equipment-total-weight")
    if weight_el:
        weight_el.textContent = f"{total_weight:.1f} lb"


# =============================================================================
# Class Features & Domain Features Databases
# =============================================================================

CLASS_FEATURES_DATABASE = {
    "cleric": {
        1: [
            {"name": "Spellcasting", "description": "You can cast cleric spells using your choice of Wisdom or Intelligence (typically Wisdom) as your spellcasting ability modifier."},
            {"name": "Channel Divinity (DC)", "description": "You can use your action and expend one spell slot to invoke devastating divine magic. You know one Channel Divinity option. You gain more options at higher levels."},
        ],
        2: [
            {"name": "Channel Divinity", "description": "You can now use your Channel Divinity twice between rests."},
        ],
        3: [],
        5: [
            {"name": "Destroy Undead", "description": "When a creature you can see within 30 feet of you drops to 0 hit points, you can use your reaction to destroy it and render it unable to be raised from the dead. You can use this feature a number of times equal to your Wisdom modifier (minimum of 1)."},
        ],
        6: [
            {"name": "Channel Divinity", "description": "You can now use your Channel Divinity three times between rests."},
        ],
        8: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1. You can't increase an ability score above 20 using this feature."},
        ],
        10: [
            {"name": "Divine Intervention", "description": "You can call on your deity for aid. Describing what aid you seek, you make a DC 10 Wisdom check. If you succeed, the deity intervenes. The GM chooses how the intervention occurs."},
        ],
        12: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
        14: [
            {"name": "Improved Divine Intervention", "description": "Your Divine Intervention DC becomes 5 instead of 10 when you reach this level."},
        ],
        16: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
        19: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
    },
    "bard": {
        1: [
            {"name": "Spellcasting", "description": "You know a number of cantrips equal to your Charisma modifier (minimum of 1). You can cast any bard spell you know, provided that you have spell slots available to cast the spell."},
            {"name": "Bardic Inspiration", "description": "You can inspire others through stirring words or music. When another creature that can hear you within 60 feet of you makes an Attack roll, ability check, or damage roll, you can use your reaction to add to that roll."},
        ],
        2: [
            {"name": "Jack of All Trades", "description": "Starting at 2nd level, you can add half your proficiency bonus (round down) to any ability check you make that doesn't already include your proficiency bonus."},
        ],
        3: [],
        5: [
            {"name": "Bardic Inspiration Die Increases", "description": "Your Bardic Inspiration die becomes a d8."},
        ],
        6: [
            {"name": "Expertise Expansion", "description": "You can choose two more of your skill proficiencies to gain expertise."},
        ],
        8: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
        10: [
            {"name": "Bardic Inspiration Die Increases", "description": "Your Bardic Inspiration die becomes a d10."},
        ],
        12: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
    },
}

# Domain-specific features for clerics
DOMAIN_FEATURES_DATABASE = {
    "life": {
        1: [
            {"name": "Bonus Proficiency", "description": "You gain proficiency with heavy armor."},
            {"name": "Disciple of Life", "description": "Your healing spells are more effective. Whenever you use a spell to restore hit points to a creature, that creature regains additional hit points equal to 2 + the spell's level."},
        ],
        2: [
            {"name": "Channel Divinity: Preserve Life", "description": "As an action, you can expend a use of your Channel Divinity to restore hit points to any number of creatures that you can see within 30 feet of you. You restore a number of hit points equal to five times your cleric level. Distribute these hit points among the creatures as you choose, but no creature can regain more than half of its maximum hit points at once."},
        ],
        6: [
            {"name": "Blessed Healer", "description": "The healing spells you cast on others can heal you as well. When you cast a healing spell whose target is not you, you regain hit points equal to 2 + the spell's level."},
        ],
        8: [
            {"name": "Divine Strike", "description": "Once on each of your turns when you hit a creature with a weapon attack, you can cause the attack to deal an extra 1d8 radiant damage to the target. When you reach 14th level, the extra damage increases to 2d8."},
        ],
        17: [
            {"name": "Supreme Healing", "description": "When you would normally roll one or more dice to restore hit points with a spell, you instead use the highest number possible for each die. For example, instead of restoring 2d6 hit points to a creature, you restore 12."},
        ],
    },
}

DOMAIN_BONUS_SPELLS = {
    "life": {
        1: ["cure-wounds", "bless"],
        3: ["lesser-restoration", "spiritual-weapon"],
        5: ["beacon-of-hope", "revivify"],
        7: ["guardian-of-faith", "death-ward"],
        9: ["mass-cure-wounds", "raise-dead"],
    },
}

# =============================================================================
# Class Features & Domain Functions
# =============================================================================

def get_class_features_for_level(class_name: str, current_level: int) -> list:
    """Get all class features up to the current level."""
    class_key = class_name.lower().strip() if class_name else ""
    features_by_level = CLASS_FEATURES_DATABASE.get(class_key, {})
    
    all_features = []
    for level in sorted(features_by_level.keys()):
        if level <= current_level:
            all_features.extend(features_by_level[level])
    return all_features


def get_domain_features_for_level(domain_name: str, current_level: int) -> list:
    """Get all domain-specific features up to the current level."""
    domain_key = domain_name.lower().strip() if domain_name else ""
    features_by_level = DOMAIN_FEATURES_DATABASE.get(domain_key, {})
    
    all_features = []
    for level in sorted(features_by_level.keys()):
        if level <= current_level:
            all_features.extend(features_by_level[level])
    return all_features


def get_domain_bonus_spells(domain_name: str, current_level: int) -> list[str]:
    """Get all domain bonus spell slugs available up to the current level."""
    domain_key = domain_name.lower().strip() if domain_name else ""
    spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
    
    bonus_spells = []
    for level in sorted(spells_by_level.keys()):
        if level <= current_level:
            bonus_spells.extend(spells_by_level[level])
    return bonus_spells


# =============================================================================
# Module Initialization - Capture Function References
# =============================================================================

def initialize_module_references():
    """Initialize references to character and export management modules.
    
    Called at module load and optionally on first handler use. Uses lazy initialization
    to handle modules that haven't loaded yet at import time, especially export_management
    which is imported after equipment_management in character.py.
    
    Important: We store MODULE references, not function references. Functions are called
    through the module to avoid PyScript/Pyodide proxy lifecycle issues where borrowed
    proxies are automatically destroyed.
    """
    global _CHAR_MODULE_REF, _EXPORT_MODULE_REF
    
    import sys
    
    # Capture main module reference (character.py) if not already done
    if _CHAR_MODULE_REF is None:
        _CHAR_MODULE_REF = sys.modules.get('__main__')
        if _CHAR_MODULE_REF:
            # Verify function exists
            if hasattr(_CHAR_MODULE_REF, 'update_calculations'):
                console.log("DEBUG: Captured __main__ module reference (update_calculations available)")
            else:
                _CHAR_MODULE_REF = None
    
    # Capture export management module reference (may not be loaded yet at module init time)
    # This uses lazy initialization - if not captured at load time, will be captured on first use
    if _EXPORT_MODULE_REF is None:
        _EXPORT_MODULE_REF = sys.modules.get('export_management')
        if _EXPORT_MODULE_REF:
            # Verify function exists
            if hasattr(_EXPORT_MODULE_REF, 'schedule_auto_export'):
                console.log("DEBUG: Captured export_management module reference (schedule_auto_export available)")
            else:
                _EXPORT_MODULE_REF = None
        else:
            console.log("DEBUG: export_management not yet in sys.modules (lazy init will retry on first use)")


# Call initialization when module loads (idempotent - safe to call multiple times)
try:
    initialize_module_references()
except Exception as e:
    console.error(f"DEBUG: Failed to initialize module references at load time: {e}")
