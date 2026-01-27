"""
Weapons Management - Manages weapon entities and displays weapons grid.

Architecture:
- WeaponEntity: Represents a single weapon with display properties
- WeaponsCollectionManager: Manages a collection of weapon entities and renders them
- Each weapon entity has properties like final_name, final_damage, final_tohit, etc.
- The manager just orchestrates - the entity knows how to display itself

This makes it easy to:
- Test individual weapons (entity independently)
- Test collection management (grid orchestration)
- Add new display properties (just add to WeaponEntity)
- Display in different formats (HTML table, JSON, etc.)
"""

import json
import re
from typing import Optional, Dict, List

from entity_manager import EntityManager

try:
    from tooltip_values import WeaponToHitValue
except ImportError:
    WeaponToHitValue = None

try:
    from js import console, document
except ImportError:
    # Mock for testing
    class _MockConsole:
        @staticmethod
        def log(msg):
            print(f"[WEAPONS] {msg}")
        
        @staticmethod
        def error(msg):
            print(f"[WEAPONS ERROR] {msg}")
    
    console = _MockConsole()


class WeaponEntity(EntityManager):
    """Represents a single weapon with all its display properties."""
    
    def __init__(self, weapon_data: Dict = None, character_stats: Dict = None):
        """Initialize weapon entity.
        
        Args:
            weapon_data: Raw weapon data from inventory
            character_stats: Character ability scores and proficiency for calculations
        """
        super().__init__(weapon_data)
        self.character_stats = character_stats or {}
    
    @property
    def final_display_value(self) -> str:
        """Return the weapon name for primary display."""
        return self.final_name
    
    @property
    def final_name(self) -> str:
        """Weapon name from entity."""
        return self.entity.get("name", "Unknown")
    
    @property
    def final_tohit(self) -> str:
        """Formatted to-hit bonus with sign (+4, -1, or —)."""
        to_hit = self._calculate_tohit()
        if to_hit == 0:
            return "—"
        elif to_hit > 0:
            return f"+{to_hit}"
        else:
            return str(to_hit)
    
    @property
    def final_damage(self) -> str:
        """Formatted damage with type and bonus (1d8 slashing +1)."""
        dmg = self.entity.get("damage", "")
        dmg_type = self.entity.get("damage_type", "")
        dmg_bonus = self.entity.get("bonus", 0)
        
        # Try to get from notes JSON if not in direct fields
        if not dmg:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    dmg = notes_data.get("damage", "")
                    dmg_type = notes_data.get("damage_type", "")
                    if not dmg_bonus or dmg_bonus == 0:
                        dmg_bonus = notes_data.get("bonus", 0)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        # Try to parse bonus from weapon name if still not found
        if not dmg_bonus or dmg_bonus == 0:
            match = re.search(r'\+(\d+)', self.entity.get("name", ""))
            if match:
                dmg_bonus = int(match.group(1))
        
        # Format the damage text
        dmg_text = dmg if dmg else ""
        if dmg_text and dmg_type:
            dmg_text = f"{dmg_text} {dmg_type}"
        if dmg_bonus and dmg_bonus > 0 and dmg_text:
            dmg_text = f"{dmg_text} +{dmg_bonus}"
        
        return dmg_text if dmg_text else "—"
    
    @property
    def final_range(self) -> str:
        """Formatted range text."""
        range_text = self.entity.get("range_text", "")
        
        # Try to get from notes JSON if not in direct field
        if not range_text:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    range_text = notes_data.get("range", "")
                    if not range_text:
                        range_text = notes_data.get("range_text", "")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return range_text if range_text else "—"
    
    @property
    def final_properties(self) -> str:
        """Formatted weapon properties."""
        props = self.entity.get("weapon_properties", "")
        
        # Try to get from notes JSON if not in direct field
        if not props:
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    props = notes_data.get("properties", "")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return props if props else "—"

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
            except (json.JSONDecodeError, KeyError, TypeError):
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
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return weight if weight else "—"

    def item_info_string_equipment_list_ctx(self) -> str:
        """Return a compact string suitable for the equipment list context.

        Example: "Longsword - 15 gp - 3 lb."""
        return f"{self.final_name} - {self.final_cost} - {self.final_weight}"

    def item_info_string_skill_grid_ctx(self) -> str:
        """Return a compact string suitable for the skill/weapons grid context.

        Example: "Longsword (+4 to hit, 1d8 slashing +1)"""
        dmg = self.final_damage if self.final_damage != "—" else ""
        return f"{self.final_name} ({self.final_tohit} to hit{', ' + dmg if dmg else ''})"    
    def _calculate_tohit(self) -> int:
        """Calculate to-hit bonus: ability_mod + proficiency + weapon_bonus."""
        try:
            # Get weapon properties for ability determination
            weapon_type = self.entity.get("weapon_type", "").lower()
            properties = self.entity.get("weapon_properties", "")
            
            # Fallback: try to extract properties from notes JSON
            if not properties:
                try:
                    notes_str = self.entity.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        notes_data = json.loads(notes_str)
                        properties = notes_data.get("properties", "")
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            # Get ability modifiers from character stats
            str_score = self.character_stats.get("str", 10)
            dex_score = self.character_stats.get("dex", 10)
            str_mod = (str_score - 10) // 2
            dex_mod = (dex_score - 10) // 2
            
            # Determine which ability to use
            is_ranged = weapon_type == "ranged" or "range" in weapon_type.lower()
            is_finesse = properties and "finesse" in properties.lower()
            
            if is_ranged:
                ability_mod = dex_mod
            elif is_finesse:
                ability_mod = max(str_mod, dex_mod)
            else:
                ability_mod = str_mod
            
            # Get proficiency
            proficiency = self.character_stats.get("proficiency", 0)
            
            # Get weapon bonus from notes JSON
            weapon_bonus = 0
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    weapon_bonus = notes_data.get("bonus", 0) or 0
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
            
            # Fallback: try to parse from name
            if not weapon_bonus:
                match = re.search(r'\+(\d+)', self.entity.get("name", ""))
                if match:
                    weapon_bonus = int(match.group(1))
            
            to_hit = ability_mod + proficiency + weapon_bonus
            return to_hit
        except Exception as e:
            console.error(f"[WEAPONS] Error calculating to-hit: {e}")
            return 0
    
    def get_tohit_breakdown(self) -> tuple:
        """Get breakdown of to-hit calculation for tooltip.
        
        Returns:
            Tuple of (ability_key, ability_mod, proficiency, weapon_bonus)
        """
        try:
            weapon_type = self.entity.get("weapon_type", "").lower()
            properties = self.entity.get("weapon_properties", "")
            
            if not properties:
                try:
                    notes_str = self.entity.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        notes_data = json.loads(notes_str)
                        properties = notes_data.get("properties", "")
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            str_score = self.character_stats.get("str", 10)
            dex_score = self.character_stats.get("dex", 10)
            str_mod = (str_score - 10) // 2
            dex_mod = (dex_score - 10) // 2
            
            is_ranged = weapon_type == "ranged" or "range" in weapon_type.lower()
            is_finesse = properties and "finesse" in properties.lower()
            
            if is_ranged:
                ability_mod = dex_mod
                ability_key = "DEX"
            elif is_finesse:
                ability_mod = max(str_mod, dex_mod)
                ability_key = "DEX" if dex_mod > str_mod else "STR"
            else:
                ability_mod = str_mod
                ability_key = "STR"
            
            proficiency = self.character_stats.get("proficiency", 0)
            
            # Get weapon bonus from notes JSON
            weapon_bonus = 0
            try:
                notes_str = self.entity.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    weapon_bonus = notes_data.get("bonus", 0) or 0
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
            
            # Fallback: try to parse from name
            if not weapon_bonus:
                match = re.search(r'\+(\d+)', self.entity.get("name", ""))
                if match:
                    weapon_bonus = int(match.group(1))
            
            return (ability_key, ability_mod, proficiency, weapon_bonus)
        except Exception as e:
            console.error(f"[WEAPONS] Error getting to-hit breakdown: {e}")
            return ("STR", 0, 0, 0)


class WeaponsCollectionManager:
    """Manages a collection of weapon entities and renders weapons grid."""
    
    def __init__(self, inventory_manager=None):
        """Initialize weapons collection manager.
        
        Args:
            inventory_manager: Reference to InventoryManager instance
        """
        self.inventory_manager = inventory_manager
        self.grid_element = None
        self.empty_state_element = None
        self.weapons: List[WeaponEntity] = []
        self.character_stats: Dict = {}
    
    # === Equipped Weapons Property ===
    
    @property
    def equipped_weapons(self) -> List[WeaponEntity]:
        """Get list of equipped weapon entities ready for table rendering.
        
        Returns:
            List of WeaponEntity objects for equipped weapons.
            Each entity has properties like final_name, final_tohit, final_damage.
        """
        if not self.inventory_manager:
            return []
        
        equipped = []
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            item_name = item.get("name", "").lower()
            
            # Only weapons, and exclude obvious armor items by name
            armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
            is_armor_by_name = any(kw in item_name for kw in armor_keywords)
            
            if item.get("equipped") and category in ["weapons", "weapon"] and not is_armor_by_name:
                weapon = WeaponEntity(item, self.character_stats)
                equipped.append(weapon)
        
        return equipped
    
    def initialize(self, character_stats: Dict = None):
        """Initialize grid elements and character stats. Call after DOM is ready."""
        self.grid_element = self._get_element("weapons-grid")
        self.empty_state_element = self._get_element("weapons-empty-state")
        self.character_stats = character_stats or {}
        if self.grid_element:
            console.log("[WEAPONS] WeaponsCollectionManager initialized")
        else:
            console.error("[WEAPONS] weapons-grid element not found")
    
    def _get_element(self, element_id: str):
        """Get element by ID, with fallback for testing."""
        try:
            return document.getElementById(element_id)
        except Exception:
            return None
    
    def render(self):
        """Render weapons grid based on equipped weapons in inventory."""
        if not self.grid_element or not self.inventory_manager:
            return
        
        console.log("[WEAPONS] render() called")
        
        # Build weapon entities from inventory
        self._build_weapon_entities()
        console.log(f"[WEAPONS] Built {len(self.weapons)} weapon entities")
        
        # Clear old weapon rows (preserve empty state row)
        self._clear_weapon_rows()
        
        # If no weapons, show empty state
        if not self.weapons:
            self._show_empty_state()
            return
        
        # Hide empty state and render weapons
        self._hide_empty_state()
        self._render_weapon_rows()
    
    def _build_weapon_entities(self):
        """Build WeaponEntity objects from equipped weapons in inventory."""
        self.weapons = []
        if not self.inventory_manager:
            return
        
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            item_name = item.get("name", "").lower()
            
            # Only weapons, and exclude obvious armor items by name
            armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
            is_armor_by_name = any(kw in item_name for kw in armor_keywords)
            
            if item.get("equipped") and category in ["weapons", "weapon"] and not is_armor_by_name:
                weapon = WeaponEntity(item, self.character_stats)
                self.weapons.append(weapon)
    
    def _clear_weapon_rows(self):
        """Remove all weapon rows except empty state."""
        if not self.grid_element:
            return
        
        rows_to_remove = []
        for row in self.grid_element.querySelectorAll("tr"):
            if row.id != "weapons-empty-state":
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
    
    def _render_weapon_rows(self):
        """Render table rows for all weapon entities."""
        if not self.grid_element:
            return
        
        for weapon in self.weapons:
            row = self._create_weapon_row(weapon)
            self.grid_element.appendChild(row)
    
    def _create_weapon_row(self, weapon: WeaponEntity) -> object:
        """Create a table row for a weapon entity."""
        try:
            row = document.createElement("tr")
            
            # Column 1: Weapon name
            name_td = document.createElement("td")
            name_td.textContent = weapon.final_name
            row.appendChild(name_td)
            
            # Column 2: To Hit bonus with tooltip
            to_hit_td = document.createElement("td")
            to_hit_text = weapon.final_tohit
            
            # Generate tooltip if WeaponToHitValue is available
            tooltip_html = ""
            if WeaponToHitValue:
                try:
                    ability_key, ability_mod, proficiency, weapon_bonus = weapon.get_tohit_breakdown()
                    console.log(f"[WEAPONS] Tooltip breakdown: {ability_key}={ability_mod}, prof={proficiency}, bonus={weapon_bonus}")
                    w2h = WeaponToHitValue(
                        weapon_name=weapon.entity.get("name", ""),
                        ability=ability_key,
                        ability_mod=ability_mod,
                        proficiency=proficiency,
                        weapon_bonus=weapon_bonus
                    )
                    tooltip_html = w2h.generate_tooltip_html()
                    console.log(f"[WEAPONS] Tooltip HTML length: {len(tooltip_html)}")
                except Exception as e:
                    console.log(f"[WEAPONS] Error creating tooltip: {e}")
            else:
                console.warn("[WEAPONS] WeaponToHitValue not available")
            
            to_hit_td.innerHTML = f'<span class="stat-value">{to_hit_text}{tooltip_html}</span>'
            row.appendChild(to_hit_td)
            
            # Column 3: Damage
            dmg_td = document.createElement("td")
            dmg_td.textContent = weapon.final_damage
            row.appendChild(dmg_td)
            
            # Column 4: Range
            range_td = document.createElement("td")
            range_td.textContent = weapon.final_range
            row.appendChild(range_td)
            
            # Column 5: Properties
            prop_td = document.createElement("td")
            prop_td.textContent = weapon.final_properties
            row.appendChild(prop_td)
            
            return row
        except Exception as e:
            console.error(f"[WEAPONS] Error creating weapon row: {e}")
            return document.createElement("tr")


# Global instance
_WEAPONS_MANAGER: Optional[WeaponsCollectionManager] = None


def get_weapons_manager() -> Optional[WeaponsCollectionManager]:
    """Get the global weapons manager instance."""
    return _WEAPONS_MANAGER


def initialize_weapons_manager(inventory_manager, character_stats: Dict = None):
    """Initialize the global weapons manager.
    
    Call this once during application startup.
    
    Args:
        inventory_manager: InventoryManager instance
        character_stats: Character ability scores and proficiency
    """
    global _WEAPONS_MANAGER
    _WEAPONS_MANAGER = WeaponsCollectionManager(inventory_manager)
    _WEAPONS_MANAGER.initialize(character_stats)
    return _WEAPONS_MANAGER
