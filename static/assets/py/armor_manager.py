"""
Armor Management - Refactored for clarity and maintainability.

Design Principles:
1. Single Source of Truth: Equipment table (inventory) is THE source of truth
   - Users add/edit items via Equipment tab
   - armor_manager only READS from inventory, never modifies
   - Multiple data sources (Open5e, manual entry) can populate inventory
   - armor_manager doesn't care HOW data got there, just displays what's there

2. Separation of Concerns: Data access, calculation, and display are separate
   - ArmorData: Reads from inventory item (notes JSON > direct fields > defaults)
   - ArmorEntity: Calculates AC with DEX modifiers
   - ArmorCollectionManager: Renders UI table

3. Explicit Types: Shield vs Armor is always explicit
4. Simple Methods: Each method has one clear purpose

Architecture:
- ArmorData: Pure data extraction from inventory item (read-only)
- ArmorEntity: Business logic for AC calculations and display (read-only)
- ArmorCollectionManager: Renders armor/shield table from inventory (read-only display)

Data Flow:
  User adds item → Equipment Table (inventory) → armor_manager reads → Display
"""

import json
from typing import Optional, Dict, List
from entity_manager import EntityManager
from game_constants import ARMOR_AC_VALUES

try:
    from js import console, document
except ImportError:
    class _MockConsole:
        @staticmethod
        def log(msg): print(f"[ARMOR] {msg}")
        @staticmethod
        def error(msg): print(f"[ARMOR ERROR] {msg}")
    console = _MockConsole()


class ArmorData:
    """Pure data accessor - extracts armor data from inventory item.
    
    READ-ONLY: This class never modifies the inventory item.
    It only reads data with clear priority: notes JSON > direct fields > defaults
    
    The inventory item is the source of truth maintained by inventory_manager.
    """
    
    def __init__(self, item: Dict):
        self.item = item  # Reference to inventory item (read-only)
        self._notes_cache = None
    
    @property
    def notes(self) -> Dict:
        """Parse notes JSON once and cache."""
        if self._notes_cache is None:
            try:
                notes_str = self.item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    self._notes_cache = json.loads(notes_str)
                else:
                    self._notes_cache = {}
            except Exception:
                self._notes_cache = {}
        return self._notes_cache
    
    @property
    def name(self) -> str:
        return self.item.get("name", "Unknown Armor")
    
    @property
    def item_id(self) -> str:
        return self.item.get("id", "unknown")
    
    @property
    def is_equipped(self) -> bool:
        return self.item.get("equipped", False)
    
    @property
    def is_shield(self) -> bool:
        """Determine if this item is a shield."""
        # Check armor_type in notes first
        armor_type = self.notes.get("armor_type", "").lower()
        if armor_type == "shield":
            return True
        
        # Check direct field
        armor_type = self.item.get("armor_type", "").lower()
        if armor_type == "shield":
            return True
        
        # Check name as fallback
        if "shield" in self.name.lower():
            return True
        
        return False
    
    @property
    def base_ac(self) -> int:
        """Get base AC value (without any modifiers).
        
        For armor: The armor's base AC (e.g., 14 for Breastplate)
        For shields: The shield's AC bonus (e.g., 2 for normal Shield)
        """
        # Priority: notes > direct field > default
        ac = self.notes.get("armor_class", None)
        if ac is not None:
            try:
                return int(ac)
            except (ValueError, TypeError):
                pass
        
        ac = self.item.get("armor_class", None)
        if ac is not None:
            try:
                return int(ac) if ac else 0
            except (ValueError, TypeError):
                pass
        
        # Default: shields get +2 if no AC specified
        if self.is_shield:
            return 2
        
        return 0
    
    @property
    def armor_type(self) -> str:
        """Get armor type: Light, Medium, Heavy, or Shield."""
        # Priority: notes > direct field > infer from name
        armor_type = self.notes.get("armor_type", "")
        if not armor_type:
            armor_type = self.item.get("armor_type", "")
        
        if armor_type:
            return armor_type
        
        # Infer from name if not explicitly set
        name_lower = self.name.lower()
        if "shield" in name_lower:
            return "Shield"
        elif any(x in name_lower for x in ["breastplate", "scale", "chain shirt", "half plate"]):
            return "Medium"
        elif any(x in name_lower for x in ["plate", "chain mail", "splint", "ring mail"]):
            return "Heavy"
        elif any(x in name_lower for x in ["leather", "padded", "studded"]):
            return "Light"
        
        return "Unknown"
    
    @property
    def material(self) -> str:
        """Get armor material."""
        material = self.notes.get("material", "")
        if not material:
            material = self.item.get("material", "")
        return material if material else "—"
    
    @property
    def stealth_disadvantage(self) -> bool:
        """Check if armor imposes stealth disadvantage."""
        return self.armor_type.lower() == "heavy"
    
    @property
    def cost(self) -> str:
        """Get armor cost."""
        cost = self.notes.get("cost", "")
        if not cost:
            cost = self.item.get("cost", "")
        return cost if cost else "—"
    
    @property
    def weight(self) -> str:
        """Get armor weight."""
        weight = self.notes.get("weight", "")
        if not weight:
            weight = self.item.get("weight", "")
        return weight if weight else "—"


class ArmorEntity(EntityManager):
    """Business logic for armor - handles AC calculations and display formatting.
    
    READ-ONLY: This class only reads from inventory data and calculates derived values.
    It never modifies the underlying inventory item.
    """
    
    def __init__(self, armor_data: Dict, character_stats: Dict = None):
        super().__init__(armor_data)
        self.data = ArmorData(armor_data)  # Read-only data accessor
        self.character_stats = character_stats or {}
    
    # === Display Properties ===
    
    @property
    def final_display_value(self) -> str:
        return self.data.name
    
    @property
    def display_name(self) -> str:
        return self.data.name
    
    @property
    def display_ac(self) -> str:
        """AC for table display.
        
        Armor: Base AC (e.g., "14")
        Shield: Bonus with + (e.g., "+2")
        """
        if self.data.is_shield:
            ac = self.data.base_ac
            return f"+{ac}" if ac > 0 else "—"
        else:
            ac = self.data.base_ac
            return str(ac) if ac > 0 else "—"
    
    @property
    def final_ac(self) -> str:
        """Total AC with DEX modifier included (for compatibility with tests and calculations).
        
        Returns formatted string: "15", "17", "3" (shield), or "—"
        Note: Shields return plain number, not +3 format (that's only for display_ac)
        """
        ac = self.calculate_total_ac()
        return str(ac) if ac > 0 else "—"
    
    @property
    def display_type(self) -> str:
        return self.data.armor_type
    
    @property
    def display_material(self) -> str:
        return self.data.material
    
    @property
    def display_stealth(self) -> str:
        return "Disadvantage" if self.data.stealth_disadvantage else "Normal"
    
    @property
    def display_cost(self) -> str:
        return self.data.cost
    
    @property
    def display_weight(self) -> str:
        return self.data.weight
    
    # === Context String Methods ===
    
    def item_info_string_equipment_list_ctx(self) -> str:
        """Return a compact string suitable for the equipment list context.
        
        Example: "Leather Armor - 10 gp - 10 lb."
        """
        return f"{self.display_name} - {self.display_cost} - {self.display_weight}"
    
    def item_info_string_character_sheet_ctx(self) -> str:
        """Return a compact string suitable for character sheet context.
        
        Example: "Leather Armor (AC 13)"
        """
        return f"{self.display_name} (AC {self.final_ac})"
    
    # === Backward Compatibility Properties ===
    
    @property
    def final_name(self) -> str:
        """Backward compatibility: alias for display_name."""
        return self.display_name
    
    @property
    def final_armor_type(self) -> str:
        """Backward compatibility: alias for display_type."""
        return self.display_type
    
    @property
    def final_armor_class(self) -> str:
        """Backward compatibility: Full AC description (e.g., 'Medium Armor 15')."""
        armor_type = self.display_type
        ac = self.final_ac
        
        if armor_type == "—" or ac == "—":
            return "—"
        
        return f"{armor_type} {ac}"
    
    @property
    def final_material(self) -> str:
        """Backward compatibility: alias for display_material."""
        return self.display_material
    
    @property
    def final_stealth(self) -> str:
        """Backward compatibility: alias for display_stealth."""
        return self.display_stealth
    
    # === Calculation Methods ===
    
    def calculate_total_ac(self) -> int:
        """Calculate total AC including DEX modifier.
        
        Used by character.py for total AC calculation.
        
        Returns:
            For armor: base AC + DEX modifier (capped by type)
            For shields: base AC bonus
        """
        if self.data.is_shield:
            return self.data.base_ac
        
        base = self.data.base_ac
        if base <= 0:
            return 0
        
        # Add DEX modifier based on armor type
        armor_type = self.data.armor_type.lower()
        
        if "light" in armor_type:
            # Light armor: full DEX modifier
            dex_mod = self._get_dex_modifier()
            return base + max(0, dex_mod)
        
        elif "medium" in armor_type:
            # Medium armor: DEX capped at +2
            dex_mod = self._get_dex_modifier()
            dex_mod = max(0, min(2, dex_mod))
            return base + dex_mod
        
        else:
            # Heavy armor: no DEX modifier
            return base
    
    def _get_dex_modifier(self) -> int:
        """Get character's DEX modifier."""
        dex_score = self.character_stats.get("dex", 10)
        return (dex_score - 10) // 2
    
    def _calculate_ac(self) -> int:
        """Backward compatibility: alias for calculate_total_ac()."""
        return self.calculate_total_ac()


class ArmorCollectionManager:
    """Manages the armor table UI - renders all armor/shields from inventory.
    
    READ-ONLY VIEWER: This class reads from inventory_manager and displays armor.
    
    Data Flow:
      inventory_manager (source of truth) → armor_manager (read & display)
    
    The ONLY way this modifies inventory is through the equipped checkbox,
    which calls inventory_manager.update_item() - the proper API.
    
    Users add/edit armor in Equipment tab, which updates inventory_manager.
    This class just reflects those changes in the Skills tab armor table.
    """
    
    def __init__(self, inventory_manager=None, character_stats: Dict = None):
        self.inventory_manager = inventory_manager
        self.character_stats = character_stats or {}
        self.armor_pieces: List[ArmorEntity] = []
        
        self.grid_element = self._get_element("armor-grid")
        self.empty_state_element = self._get_element("armor-empty-state")
        
        if self.grid_element:
            console.log("[ARMOR] ArmorCollectionManager initialized")
        else:
            console.error("[ARMOR] armor-grid element not found")
    
    # === AC Calculation Properties (Single Source of Truth) ===
    
    @property
    def armor_ac(self) -> int:
        """Get AC from equipped armor piece only (includes DEX modifier if applicable).
        
        Returns:
            - If armor equipped: base armor AC + DEX modifier (capped by armor type)
            - If no armor: 0 (unarmored AC calculated separately)
        """
        if not self.inventory_manager:
            return 0
        
        for item in self.inventory_manager.items:
            if not item.get("equipped"):
                continue
            
            category = item.get("category", "").lower()
            if category not in ["armor", "armour", "shield"]:
                continue
            
            armor_entity = ArmorEntity(item, self.character_stats)
            
            if not armor_entity.data.is_shield:
                # Found equipped armor piece
                return armor_entity.calculate_total_ac()
        
        return 0  # No armor equipped
    
    @property
    def shield_ac(self) -> int:
        """Get total AC bonus from equipped shields.
        
        Returns:
            Sum of all equipped shield AC values (typically 2 per shield)
        """
        if not self.inventory_manager:
            return 0
        
        total_shield_bonus = 0
        
        for item in self.inventory_manager.items:
            if not item.get("equipped"):
                continue
            
            category = item.get("category", "").lower()
            if category not in ["armor", "armour", "shield"]:
                continue
            
            armor_entity = ArmorEntity(item, self.character_stats)
            
            if armor_entity.data.is_shield:
                total_shield_bonus += armor_entity.data.base_ac
        
        return total_shield_bonus
    
    @property
    def other_ac(self) -> int:
        """Get AC from non-armor sources (shields, magic items, etc.).
        
        Currently this is just shields, but could be extended for rings,
        cloaks, or other AC-granting items.
        
        Returns:
            Total AC bonus from shields and other non-armor sources
        """
        return self.shield_ac
    
    @property
    def total_ac(self) -> int:
        """Get complete AC calculation (armor + shields + modifiers).
        
        This is the authoritative AC calculation:
        - If armor equipped: armor AC (with DEX) + shield AC
        - If no armor: unarmored AC (10 + DEX) + shield AC
        
        Returns:
            Total AC value for the character
        """
        if not self.inventory_manager:
            # No inventory - use unarmored AC
            dex_mod = (self.character_stats.get("dex", 10) - 10) // 2
            return 10 + dex_mod
        
        armor_ac = self.armor_ac
        
        if armor_ac > 0:
            # Wearing armor: use armor AC + shields
            base_ac = armor_ac
        else:
            # Not wearing armor: use unarmored AC (10 + DEX)
            dex_mod = (self.character_stats.get("dex", 10) - 10) // 2
            base_ac = 10 + dex_mod
        
        total = base_ac + self.shield_ac
        return max(1, total)
    
    # === Armor List Properties ===
    
    @property
    def equipped_armor_items(self) -> List[ArmorEntity]:
        """Get list of equipped armor/shield entities for armor table.
        
        Returns:
            List of ArmorEntity objects for equipped armor and shields.
            Each entity has properties like final_name, final_ac, final_armor_type.
        """
        if not self.inventory_manager:
            return []
        
        equipped = []
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            is_armor = category in ["armor", "armour", "shield"]
            
            if is_armor and item.get("equipped"):
                armor = ArmorEntity(item, self.character_stats)
                equipped.append(armor)
        
        return equipped
    
    @property
    def unequipped_armor_items(self) -> List[ArmorEntity]:
        """Get list of unequipped armor/shield entities (in backpack).
        
        Returns:
            List of ArmorEntity objects for armor/shields not currently equipped.
        """
        if not self.inventory_manager:
            return []
        
        unequipped = []
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            is_armor = category in ["armor", "armour", "shield"]
            
            if is_armor and not item.get("equipped"):
                armor = ArmorEntity(item, self.character_stats)
                unequipped.append(armor)
        
        return unequipped
    
    @property
    def all_armor_items(self) -> List[ArmorEntity]:
        """Get list of all armor/shield entities (equipped + unequipped).
        
        Returns:
            List of all ArmorEntity objects in inventory.
        """
        if not self.inventory_manager:
            return []
        
        all_items = []
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            is_armor = category in ["armor", "armour", "shield"]
            
            if is_armor:
                armor = ArmorEntity(item, self.character_stats)
                all_items.append(armor)
        
        return all_items
    
    def _get_element(self, element_id: str):
        """Get element by ID, with fallback for testing."""
        try:
            return document.getElementById(element_id)
        except Exception:
            return None
    
    def render(self):
        """Render armor table showing all armor/shields from inventory."""
        if not self.grid_element or not self.inventory_manager:
            return
        
        console.log("[ARMOR] render() called")
        
        # Build armor entities from inventory
        self._build_armor_entities()
        console.log(f"[ARMOR] Found {len(self.armor_pieces)} armor/shield items")
        
        # Clear table
        self._clear_table()
        
        # Show empty state if no armor
        if not self.armor_pieces:
            self._show_empty_state()
            return
        
        # Render armor rows
        self._hide_empty_state()
        for armor in self.armor_pieces:
            row = self._create_armor_row(armor)
            self.grid_element.appendChild(row)
    
    def _build_armor_entities(self):
        """Build ArmorEntity objects from all armor/shields in inventory."""
        self.armor_pieces = []
        if not self.inventory_manager:
            return
        
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            is_armor = category in ["armor", "armour", "shield"]
            
            if is_armor:
                armor = ArmorEntity(item, self.character_stats)
                self.armor_pieces.append(armor)
    
    def _clear_table(self):
        """Remove all armor rows except empty state."""
        if not self.grid_element:
            return
        
        rows = list(self.grid_element.children)
        for row in rows:
            if row.id != "armor-empty-state":
                self.grid_element.removeChild(row)
    
    def _show_empty_state(self):
        if self.empty_state_element:
            self.empty_state_element.style.display = "table-row"
    
    def _hide_empty_state(self):
        if self.empty_state_element:
            self.empty_state_element.style.display = "none"
    
    def _create_armor_row(self, armor: ArmorEntity) -> object:
        """Create a table row for an armor or shield."""
        try:
            row = document.createElement("tr")
            row.id = f"armor-row-{armor.data.item_id}"
            
            # Column 1: Name
            name_td = document.createElement("td")
            name_td.textContent = armor.display_name
            if armor.data.is_shield:
                name_td.style.color = "green"
            row.appendChild(name_td)
            
            # Column 2: AC
            ac_td = document.createElement("td")
            ac_td.textContent = armor.display_ac
            row.appendChild(ac_td)
            
            # Column 3: Type
            type_td = document.createElement("td")
            type_td.textContent = armor.display_type
            row.appendChild(type_td)
            
            # Column 4: Material
            material_td = document.createElement("td")
            material_td.textContent = armor.display_material
            row.appendChild(material_td)
            
            # Column 5: Stealth
            stealth_td = document.createElement("td")
            stealth_td.textContent = armor.display_stealth
            if armor.data.stealth_disadvantage:
                stealth_td.style.color = "red"
            row.appendChild(stealth_td)
            
            # Column 6: Equipped checkbox
            equipped_td = document.createElement("td")
            equipped_td.style.textAlign = "center"
            
            checkbox = document.createElement("input")
            checkbox.type = "checkbox"
            checkbox.checked = armor.data.is_equipped
            checkbox.style.cursor = "pointer"
            checkbox.id = f"armor-equipped-{armor.data.item_id}"
            
            # Event handler
            checkbox.addEventListener("change", 
                lambda event: self._handle_equipped_change(event, armor.data.item_id))
            
            equipped_td.appendChild(checkbox)
            row.appendChild(equipped_td)
            
            return row
        except Exception as e:
            console.error(f"[ARMOR] Error creating armor row: {e}")
            return document.createElement("tr")
    
    def _handle_equipped_change(self, event, armor_id: str):
        """Handle armor equipped checkbox change.
        
        This is the ONLY place armor_manager modifies inventory data.
        It properly goes through inventory_manager.update_item() API.
        
        Updates inventory (source of truth) → triggers recalculation → re-renders
        """
        try:
            if not self.inventory_manager:
                return
            
            is_equipped = event.target.checked
            
            # Update inventory through proper API (source of truth)
            self.inventory_manager.update_item(armor_id, {"equipped": is_equipped})
            
            # Recalculate character AC
            try:
                import sys
                char_module = sys.modules.get('character')
                if char_module:
                    calc_ac = getattr(char_module, 'calculate_armor_class', None)
                    update_calc = getattr(char_module, 'update_calculations', None)
                    if calc_ac:
                        calc_ac()
                    if update_calc:
                        update_calc()
                else:
                    console.warn("[ARMOR] character module not in sys.modules")
            except Exception as e:
                console.error(f"[ARMOR] Error updating calculations: {e}")
            
            # Re-render
            self.render()
            
            console.log(f"[ARMOR] Armor {armor_id} equipped: {is_equipped}")
        except Exception as e:
            console.error(f"[ARMOR] Error handling equipped change: {e}")


# === Global Instance ===

_ARMOR_MANAGER: Optional[ArmorCollectionManager] = None


def get_armor_manager() -> Optional[ArmorCollectionManager]:
    """Get the global armor manager instance."""
    return _ARMOR_MANAGER


def calculate_total_ac_from_armor_manager(inventory_manager, character_stats: Dict) -> int:
    """Calculate total AC using armor_manager logic (single source of truth).
    
    This is the authoritative AC calculation that uses the same logic as the armor table.
    Now simplified to use the ArmorCollectionManager properties.
    
    Args:
        inventory_manager: Inventory manager with armor/shield items
        character_stats: Character stats dict with 'dex' key
    
    Returns:
        Total AC = armor AC + shield AC, or unarmored AC if no armor
    """
    if not inventory_manager:
        # No inventory - use unarmored AC
        dex_mod = (character_stats.get("dex", 10) - 10) // 2
        return 10 + dex_mod
    
    # Create temporary manager to use properties
    temp_manager = ArmorCollectionManager(inventory_manager, character_stats)
    
    # Use the properties for calculation
    total_ac = temp_manager.total_ac
    
    console.log(f"[ARMOR-AC] Total AC: {temp_manager.armor_ac} (armor) + {temp_manager.shield_ac} (shields) = {total_ac}")
    return total_ac


# === Manager Set Methods (for event handlers) ===

def set_armor_ac(inventory_manager, item_id: str, ac_value: int) -> bool:
    """
    Set the armor_class value for an armor/shield item.
    
    Args:
        inventory_manager: The inventory manager instance
        item_id: The item ID to update
        ac_value: The new AC value (total, including bonuses)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        item = inventory_manager.get_item(item_id)
        if not item:
            console.error(f"[ARMOR-SET] Item {item_id} not found")
            return False
        
        # Parse existing notes to preserve other properties
        notes_str = item.get("notes", "")
        if notes_str and notes_str.startswith("{"):
            extra_props = json.loads(notes_str)
        else:
            extra_props = {}
        
        # Update armor_class
        extra_props["armor_class"] = ac_value
        
        # Save back to notes
        notes = json.dumps(extra_props) if extra_props else ""
        inventory_manager.update_item(item_id, {"notes": notes})
        
        console.log(f"[ARMOR-SET] Set AC for {item.get('name')} to {ac_value}")
        return True
    except Exception as e:
        console.error(f"[ARMOR-SET] Error setting AC: {e}")
        return False


def set_armor_bonus(inventory_manager, item_id: str, bonus_value: int) -> bool:
    """
    Set the magical bonus for an armor/shield item and auto-calculate total AC.
    
    This is the preferred method for bonus changes as it handles all calculation logic.
    
    Args:
        inventory_manager: The inventory manager instance
        item_id: The item ID to update
        bonus_value: The magical bonus value (+0, +1, +2, etc.)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        item = inventory_manager.get_item(item_id)
        if not item:
            console.error(f"[ARMOR-SET] Item {item_id} not found")
            return False
        
        # Parse existing notes to preserve other properties
        notes_str = item.get("notes", "")
        if notes_str and notes_str.startswith("{"):
            extra_props = json.loads(notes_str)
        else:
            extra_props = {}
        
        # Determine if this is a shield
        armor_name = item.get("name", "").lower()
        is_shield = "shield" in armor_name
        
        if bonus_value != 0:
            # Store bonus in notes
            extra_props["bonus"] = bonus_value
            
            if is_shield:
                # Shields: base AC is 2, total = base + bonus
                total_ac = 2 + bonus_value
                extra_props["armor_class"] = total_ac
                console.log(f"[ARMOR-SET] Shield {item.get('name')}: AC = 2 + {bonus_value} = {total_ac}")
            else:
                # Regular armor: find base AC from ARMOR_AC_VALUES
                base_ac = None
                for armor_key, ac_value in ARMOR_AC_VALUES.items():
                    if armor_key in armor_name:
                        base_ac = ac_value
                        break
                if base_ac is None:
                    base_ac = 10  # Default fallback
                total_ac = base_ac + bonus_value
                extra_props["armor_class"] = total_ac
                console.log(f"[ARMOR-SET] Armor {item.get('name')}: AC = {base_ac} + {bonus_value} = {total_ac}")
        else:
            # bonus_value is 0, remove bonus and reset to base
            if "bonus" in extra_props:
                del extra_props["bonus"]
            
            if is_shield:
                extra_props["armor_class"] = 2
                console.log(f"[ARMOR-SET] Shield {item.get('name')}: Reset to base AC 2")
            else:
                # For armor, reset to base AC
                base_ac = None
                for armor_key, ac_value in ARMOR_AC_VALUES.items():
                    if armor_key in armor_name:
                        base_ac = ac_value
                        break
                if base_ac:
                    extra_props["armor_class"] = base_ac
                    console.log(f"[ARMOR-SET] Armor {item.get('name')}: Reset to base AC {base_ac}")
                elif "armor_class" in extra_props:
                    del extra_props["armor_class"]
        
        # Save back to notes
        notes = json.dumps(extra_props) if extra_props else ""
        inventory_manager.update_item(item_id, {"notes": notes})
        
        console.log(f"[ARMOR-SET] Set bonus for {item.get('name')} to {bonus_value}")
        return True
    except Exception as e:
        console.error(f"[ARMOR-SET] Error setting bonus: {e}")
        return False


def initialize_armor_manager(inventory_manager, character_stats: Dict = None):
    """Initialize the global armor manager."""
    global _ARMOR_MANAGER
    _ARMOR_MANAGER = ArmorCollectionManager(inventory_manager, character_stats)
    console.log("[ARMOR] Armor manager initialized")
    return _ARMOR_MANAGER


def render_armor_grid():
    """Render the armor grid (public API)."""
    if _ARMOR_MANAGER:
        _ARMOR_MANAGER.render()
