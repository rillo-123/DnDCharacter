"""
Armor Management - Manages armor entities and displays armor grid.

Architecture:
- ArmorEntity: Represents a single armor with display properties
- ArmorCollectionManager: Manages a collection of armor entities and renders them
- Each armor entity has properties like final_name, final_ac, final_type, etc.
- The manager just orchestrates - the entity knows how to display itself

This follows the same pattern as WeaponsManager for consistency.
"""

import json
import re
from typing import Optional, Dict, List

from entity_manager import EntityManager

try:
    from js import console, document
except ImportError:
    # Mock for testing
    class _MockConsole:
        @staticmethod
        def log(msg):
            print(f"[ARMOR] {msg}")
        
        @staticmethod
        def error(msg):
            print(f"[ARMOR ERROR] {msg}")
    
    console = _MockConsole()


class ArmorEntity(EntityManager):
    """Represents a single armor piece with all its display properties."""
    
    def __init__(self, armor_data: Dict = None, character_stats: Dict = None):
        """Initialize armor entity.
        
        Args:
            armor_data: Raw armor data from inventory
            character_stats: Character ability scores and proficiency for calculations
        """
        super().__init__(armor_data)
        self.character_stats = character_stats or {}
    
    @property
    def final_display_value(self) -> str:
        """Return the armor name for primary display."""
        return self.final_name
    
    @property
    def final_name(self) -> str:
        """Armor name from entity."""
        return self.entity.get("name", "Unknown")
    
    @property
    def final_ac(self) -> str:
        """Formatted armor class value."""
        ac = self._calculate_ac()
        return str(ac) if ac > 0 else "—"
    
    @property
    def final_armor_type(self) -> str:
        """Type of armor (Light, Medium, Heavy, or Shield)."""
        armor_type = self.entity.get("armor_type", "")
        
        # Try to get from notes JSON if not in direct field
        if not armor_type:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    armor_type = notes_data.get("armor_type", "")
            except:
                pass
        
        return armor_type if armor_type else "—"
    
    @property
    def final_armor_class(self) -> str:
        """Full AC description (Light Armor 12, Heavy Armor 16, etc)."""
        armor_type = self.final_armor_type
        ac = self.final_ac
        
        if armor_type == "—" or ac == "—":
            return "—"
        
        return f"{armor_type} {ac}"
    
    @property
    def final_material(self) -> str:
        """Material composition (Leather, Chain Mail, Plate, etc)."""
        material = self.entity.get("material", "")
        
        # Try to get from notes JSON if not in direct field
        if not material:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    material = notes_data.get("material", "")
            except:
                pass
        
        return material if material else "—"

    @property
    def final_cost(self) -> str:
        """Formatted cost string for equipment lists (e.g., '15 gp')."""
        cost = self.entity.get("cost", "")
        if not cost:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    cost = notes_data.get("cost", "")
            except:
                pass
        return cost if cost else "—"

    @property
    def final_weight(self) -> str:
        """Formatted weight string for equipment lists (e.g., '3 lb.')."""
        weight = self.entity.get("weight", "")
        if not weight:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    weight = notes_data.get("weight", "")
            except:
                pass
        return weight if weight else "—"

    def item_info_string_equipment_list_ctx(self) -> str:
        """Return a compact string suitable for the equipment list context.

        Example: "Leather Armor - 10 gp - 10 lb."""
        return f"{self.final_name} - {self.final_cost} - {self.final_weight}"

    def item_info_string_character_sheet_ctx(self) -> str:
        """Return a compact string suitable for character sheet context.

        Example: "Leather Armor (AC 13)"""
        return f"{self.final_name} (AC {self.final_ac})"    
    @property
    def final_stealth(self) -> str:
        """Stealth disadvantage indicator."""
        stealth = self.entity.get("stealth_disadvantage", False)
        
        # Try to get from notes JSON if not in direct field
        if not stealth:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    stealth = notes_data.get("stealth_disadvantage", False)
            except:
                pass
        
        return "Disadvantage" if stealth else "—"
    
    def _calculate_ac(self) -> int:
        """Calculate armor class based on armor type and character stats.
        
        For light/medium armor, may add DEX modifier.
        For heavy armor, no DEX added.
        """
        try:
            base_ac = self.entity.get("armor_class", 0)
            if not base_ac:
                # Try to get from notes JSON
                try:
                    notes_str = self.entity.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        notes_data = json.loads(notes_str)
                        base_ac = notes_data.get("armor_class", 0)
                except:
                    pass
            
            if base_ac <= 0:
                return 0
            
            # Determine if we add DEX modifier
            armor_type = self.final_armor_type.lower()
            add_dex = "light" in armor_type or "medium" in armor_type
            
            if add_dex and "heavy" not in armor_type and "shield" not in armor_type:
                # Get DEX modifier
                dex_score = self.character_stats.get("dex", 10)
                dex_mod = (dex_score - 10) // 2
                return base_ac + dex_mod
            
            return base_ac
        except Exception as e:
            console.error(f"[ARMOR] Error calculating AC: {e}")
            return 0


class ArmorCollectionManager:
    """Manages a collection of armor entities and renders armor grid."""
    
    def __init__(self, inventory_manager=None):
        """Initialize armor collection manager.
        
        Args:
            inventory_manager: Reference to InventoryManager instance
        """
        self.inventory_manager = inventory_manager
        self.grid_element = None
        self.empty_state_element = None
        self.armor_pieces: List[ArmorEntity] = []
        self.character_stats: Dict = {}
    
    def initialize(self, character_stats: Dict = None):
        """Initialize grid elements and character stats. Call after DOM is ready."""
        self.grid_element = self._get_element("armor-grid")
        self.empty_state_element = self._get_element("armor-empty-state")
        self.character_stats = character_stats or {}
        if self.grid_element:
            console.log("[ARMOR] ArmorCollectionManager initialized")
        else:
            console.error("[ARMOR] armor-grid element not found")
    
    def _get_element(self, element_id: str):
        """Get element by ID, with fallback for testing."""
        try:
            return document.getElementById(element_id)
        except:
            return None
    
    def render(self):
        """Render armor grid based on equipped armor in inventory."""
        if not self.grid_element or not self.inventory_manager:
            return
        
        console.log("[ARMOR] render() called")
        
        # Build armor entities from inventory
        self._build_armor_entities()
        console.log(f"[ARMOR] Built {len(self.armor_pieces)} armor entities")
        
        # Clear old armor rows (preserve empty state row)
        self._clear_armor_rows()
        
        # If no armor, show empty state
        if not self.armor_pieces:
            self._show_empty_state()
            return
        
        # Hide empty state and render armor
        self._hide_empty_state()
        self._render_armor_rows()
    
    def _build_armor_entities(self):
        """Build ArmorEntity objects from equipped armor in inventory."""
        self.armor_pieces = []
        if not self.inventory_manager:
            return
        
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            # Accept both armor/armour and shield (UK/US insensitive)
            is_armor = category in ["armor", "armour", "shield"]
            if item.get("equipped") and is_armor:
                armor = ArmorEntity(item, self.character_stats)
                self.armor_pieces.append(armor)
    
    def _clear_armor_rows(self):
        """Remove all armor rows except empty state."""
        if not self.grid_element:
            return
        
        rows_to_remove = []
        for row in self.grid_element.querySelectorAll("tr"):
            if row.id != "armor-empty-state":
                rows_to_remove.append(row)
        
        for row in rows_to_remove:
            row.remove()
    
    def _show_empty_state(self):
        """Show the empty state message."""
        if self.empty_state_element:
            self.empty_state_element.style.display = "table-row"
    
    def _hide_empty_state(self):
        """Hide the empty state message."""
        if self.empty_state_element:
            self.empty_state_element.style.display = "none"
    
    def _render_armor_rows(self):
        """Render table rows for all armor entities."""
        if not self.grid_element:
            return
        
        for armor in self.armor_pieces:
            row = self._create_armor_row(armor)
            self.grid_element.appendChild(row)
    
    def _create_armor_row(self, armor: ArmorEntity) -> object:
        """Create a table row for an armor entity with equipped checkbox."""
        try:
            row = document.createElement("tr")
            row.id = f"armor-row-{armor.entity.get('id', 'unknown')}"
            
            # Column 1: Armor name
            name_td = document.createElement("td")
            name_td.textContent = armor.final_name
            row.appendChild(name_td)
            
            # Column 2: AC
            ac_td = document.createElement("td")
            ac_td.textContent = armor.final_ac
            row.appendChild(ac_td)
            
            # Column 3: Armor Type
            type_td = document.createElement("td")
            type_td.textContent = armor.final_armor_type
            row.appendChild(type_td)
            
            # Column 4: Material
            material_td = document.createElement("td")
            material_td.textContent = armor.final_material
            row.appendChild(material_td)
            
            # Column 5: Stealth
            stealth_td = document.createElement("td")
            stealth_td.textContent = armor.final_stealth
            row.appendChild(stealth_td)
            
            # Column 6: Equipped checkbox
            equipped_td = document.createElement("td")
            equipped_td.style.textAlign = "center"
            checkbox = document.createElement("input")
            checkbox.type = "checkbox"
            checkbox.checked = armor.entity.get("equipped", False)
            checkbox.style.cursor = "pointer"
            checkbox.id = f"armor-equipped-{armor.entity.get('id', 'unknown')}"
            
            # Add event handler for equip/unequip
            armor_id = armor.entity.get("id")
            checkbox.addEventListener("change", lambda event: self._handle_armor_equipped_change(event, armor_id))
            
            equipped_td.appendChild(checkbox)
            row.appendChild(equipped_td)
            
            return row
        except Exception as e:
            console.error(f"[ARMOR] Error creating armor row: {e}")
            return document.createElement("tr")
    
    def _handle_armor_equipped_change(self, event, armor_id: str):
        """Handle armor equipped checkbox change."""
        try:
            if not self.inventory_manager:
                return
            
            is_equipped = event.target.checked
            
            # Update the armor item's equipped status
            self.inventory_manager.update_item(armor_id, {"equipped": is_equipped})
            
            # Recalculate AC and trigger character update
            try:
                from character import calculate_armor_class, update_calculations
                calculate_armor_class()
                update_calculations()
            except:
                pass
            
            # Re-render the armor grid
            self.render()
            
            console.log(f"[ARMOR] Armor {armor_id} equipped: {is_equipped}")
        except Exception as e:
            console.error(f"[ARMOR] Error handling armor equipped change: {e}")


# Global instance
_ARMOR_MANAGER: Optional[ArmorCollectionManager] = None


def get_armor_manager() -> Optional[ArmorCollectionManager]:
    """Get the global armor manager instance."""
    return _ARMOR_MANAGER


def initialize_armor_manager(inventory_manager, character_stats: Dict = None):
    """Initialize the global armor manager.
    
    Call this once during application startup.
    
    Args:
        inventory_manager: InventoryManager instance
        character_stats: Character ability scores and proficiency
    """
    global _ARMOR_MANAGER
    _ARMOR_MANAGER = ArmorCollectionManager(inventory_manager)
    _ARMOR_MANAGER.initialize(character_stats)
    return _ARMOR_MANAGER
