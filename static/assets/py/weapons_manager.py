"""
Weapons Manager - Single source of truth for weapons grid display and management.

This module consolidates all weapons-related logic:
- Weapon data extraction and validation
- Damage and to-hit calculations
- Grid rendering with automatic updates
- Synchronization with inventory changes

This eliminates cross-module complexity and makes weapons management maintainable.
"""

import json
import re
from typing import Optional, Dict, List

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


class WeaponsManager:
    """Manages weapons grid display and synchronization with inventory."""
    
    def __init__(self, inventory_manager=None):
        """Initialize weapons manager.
        
        Args:
            inventory_manager: Reference to InventoryManager instance
        """
        self.inventory_manager = inventory_manager
        self.grid_element = None
        self.empty_state_element = None
    
    def initialize(self):
        """Initialize grid elements. Call after DOM is ready."""
        self.grid_element = self._get_element("weapons-grid")
        self.empty_state_element = self._get_element("weapons-empty-state")
        if self.grid_element:
            console.log("[WEAPONS] WeaponsManager initialized")
        else:
            console.error("[WEAPONS] weapons-grid element not found")
    
    def _get_element(self, element_id: str):
        """Get element by ID, with fallback for testing."""
        try:
            return document.getElementById(element_id)
        except:
            return None
    
    def render(self):
        """Render weapons grid based on equipped weapons in inventory."""
        if not self.grid_element or not self.inventory_manager:
            return
        
        console.log("[WEAPONS] render() called")
        
        # Get equipped weapons from inventory
        equipped_weapons = self._get_equipped_weapons()
        console.log(f"[WEAPONS] Found {len(equipped_weapons)} equipped weapons")
        
        # Clear old weapon rows (preserve empty state row)
        self._clear_weapon_rows()
        
        # If no weapons, show empty state
        if not equipped_weapons:
            self._show_empty_state()
            return
        
        # Hide empty state and render weapons
        self._hide_empty_state()
        self._render_weapon_rows(equipped_weapons)
    
    def _get_equipped_weapons(self) -> List[Dict]:
        """Get list of equipped weapons from inventory."""
        if not self.inventory_manager:
            return []
        
        equipped = []
        for item in self.inventory_manager.items:
            category = item.get("category", "").lower()
            if item.get("equipped") and category in ["weapons", "weapon"]:
                equipped.append(item)
        
        return equipped
    
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
    
    def _render_weapon_rows(self, weapons: List[Dict]):
        """Render table rows for equipped weapons."""
        if not self.grid_element:
            return
        
        for weapon in weapons:
            row = self._create_weapon_row(weapon)
            self.grid_element.appendChild(row)
    
    def _create_weapon_row(self, weapon: Dict) -> object:
        """Create a table row for a weapon."""
        try:
            row = document.createElement("tr")
            
            # Column 1: Weapon name
            name_td = document.createElement("td")
            name_td.textContent = weapon.get("name", "Unknown")
            row.appendChild(name_td)
            
            # Column 2: To Hit bonus
            to_hit_td = document.createElement("td")
            to_hit = self.calculate_weapon_tohit(weapon)
            to_hit_td.textContent = self._format_bonus(to_hit)
            row.appendChild(to_hit_td)
            
            # Column 3: Damage
            dmg_td = document.createElement("td")
            dmg_text = self._extract_damage_text(weapon)
            dmg_td.textContent = dmg_text
            row.appendChild(dmg_td)
            
            # Column 4: Range
            range_td = document.createElement("td")
            range_text = self._extract_range_text(weapon)
            range_td.textContent = range_text
            row.appendChild(range_td)
            
            # Column 5: Properties
            prop_td = document.createElement("td")
            props_text = self._extract_properties_text(weapon)
            prop_td.textContent = props_text
            row.appendChild(prop_td)
            
            return row
        except Exception as e:
            console.error(f"[WEAPONS] Error creating weapon row: {e}")
            return document.createElement("tr")
    
    def _extract_damage_text(self, weapon: Dict) -> str:
        """Extract and format damage text from weapon data."""
        dmg = weapon.get("damage", "")
        dmg_type = weapon.get("damage_type", "")
        dmg_bonus = weapon.get("bonus", 0)
        
        # Try to get from notes JSON if not in direct fields
        if not dmg:
            try:
                notes_str = weapon.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    dmg = notes_data.get("damage", "")
                    dmg_type = notes_data.get("damage_type", "")
                    if not dmg_bonus or dmg_bonus == 0:
                        dmg_bonus = notes_data.get("bonus", 0)
            except:
                pass
        
        # Try to parse bonus from weapon name if still not found
        if not dmg_bonus or dmg_bonus == 0:
            match = re.search(r'\+(\d+)', weapon.get("name", ""))
            if match:
                dmg_bonus = int(match.group(1))
        
        # Format the damage text
        dmg_text = dmg if dmg else ""
        if dmg_text and dmg_type:
            dmg_text = f"{dmg_text} {dmg_type}"
        if dmg_bonus and dmg_bonus > 0:
            dmg_text = f"{dmg_text} +{dmg_bonus}"
        
        return dmg_text if dmg_text else "—"
    
    def _extract_range_text(self, weapon: Dict) -> str:
        """Extract and format range text from weapon data."""
        range_text = weapon.get("range_text", "")
        
        # Try to get from notes JSON if not in direct field
        if not range_text:
            try:
                notes_str = weapon.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    range_text = notes_data.get("range", "")
                    if not range_text:
                        range_text = notes_data.get("range_text", "")
            except:
                pass
        
        return range_text if range_text else "—"
    
    def _extract_properties_text(self, weapon: Dict) -> str:
        """Extract and format properties text from weapon data."""
        props = weapon.get("weapon_properties", "")
        
        # Try to get from notes JSON if not in direct field
        if not props:
            try:
                notes_str = weapon.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    props = notes_data.get("properties", "")
            except:
                pass
        
        return props if props else "—"
    
    def calculate_weapon_tohit(self, weapon: Dict) -> int:
        """Calculate to-hit bonus for a weapon.
        
        Includes: ability modifier + proficiency + weapon bonus
        """
        from character import (
            gather_scores, compute_proficiency, get_numeric_value,
            determine_melee_ability_mod, determine_ranged_ability_mod
        )
        
        try:
            # Get weapon properties
            weapon_type = weapon.get("weapon_type", "").lower()
            properties = weapon.get("weapon_properties", "")
            
            # Fallback: try to extract properties from notes JSON
            if not properties:
                try:
                    notes_str = weapon.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        notes_data = json.loads(notes_str)
                        properties = notes_data.get("properties", "")
                except:
                    pass
            
            # Get ability scores
            scores = gather_scores()
            str_mod = (scores.get("str", 10) - 10) // 2
            dex_mod = (scores.get("dex", 10) - 10) // 2
            
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
            level = get_numeric_value("level", 1)
            proficiency = compute_proficiency(level)
            
            # Add weapon bonus
            weapon_bonus = weapon.get("bonus", 0)
            if not weapon_bonus:
                # Try to parse from name
                match = re.search(r'\+(\d+)', weapon.get("name", ""))
                if match:
                    weapon_bonus = int(match.group(1))
            
            to_hit = ability_mod + proficiency + weapon_bonus
            return to_hit
        except Exception as e:
            console.error(f"[WEAPONS] Error calculating to-hit: {e}")
            return 0
    
    def _format_bonus(self, bonus: int) -> str:
        """Format a numeric bonus with sign."""
        if bonus == 0:
            return "—"
        elif bonus > 0:
            return f"+{bonus}"
        else:
            return str(bonus)


# Global instance
_WEAPONS_MANAGER: Optional[WeaponsManager] = None


def get_weapons_manager() -> Optional[WeaponsManager]:
    """Get the global weapons manager instance."""
    return _WEAPONS_MANAGER


def initialize_weapons_manager(inventory_manager):
    """Initialize the global weapons manager.
    
    Call this once during application startup.
    """
    global _WEAPONS_MANAGER
    _WEAPONS_MANAGER = WeaponsManager(inventory_manager)
    _WEAPONS_MANAGER.initialize()
    return _WEAPONS_MANAGER
