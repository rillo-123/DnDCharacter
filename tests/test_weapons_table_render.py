"""Test weapon table rendering to verify damage and range display."""
import sys
import json
from pathlib import Path

# Setup path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "static" / "assets" / "py"))

import character
from character import (
    Weapon, InventoryManager, DEFAULT_STATE, 
    _enrich_weapon_item, _get_builtin_equipment_list
)


class MockElement:
    """Mock DOM element for testing."""
    def __init__(self):
        self.textContent = ""
        self.innerHTML = ""
        self.classList = set()
        self.children = []
        self.style = {}
    
    def appendChild(self, child):
        """Add a child element."""
        self.children.append(child)
    
    def querySelectorAll(self, selector):
        """Mock querySelectorAll."""
        return []
    
    def remove(self):
        """Mock remove method."""
        pass
    
    def createElement(self, tag):
        """Mock createElement."""
        return MockElement()


class MockDocument:
    """Mock document object for testing."""
    def __init__(self):
        self.elements = {}
    
    def getElementById(self, element_id):
        """Get element by ID."""
        if element_id not in self.elements:
            self.elements[element_id] = MockElement()
        return self.elements[element_id]
    
    def createElement(self, tag):
        """Create a new element."""
        elem = MockElement()
        elem.tagName = tag.upper()
        return elem


def test_weapon_enrichment_with_dagger():
    """Test that Dagger enrichment returns damage."""
    dagger = {
        "name": "Dagger",
        "equipped": True,
        "category": "Weapons"
    }
    
    enriched = _enrich_weapon_item(dagger)
    print(f"Dagger enriched: {enriched}")
    
    # Should have damage from builtin equipment
    assert enriched.get("damage"), f"Expected damage for Dagger, got: {enriched}"
    assert enriched.get("damage_type"), f"Expected damage_type for Dagger, got: {enriched}"
    assert "1d4" in enriched.get("damage", ""), f"Expected 1d4 damage for Dagger, got: {enriched.get('damage')}"
    assert "piercing" in enriched.get("damage_type", ""), f"Expected piercing damage type, got: {enriched.get('damage_type')}"


def test_weapon_enrichment_with_crossbow():
    """Test that Light Crossbow enrichment returns damage and range."""
    crossbow = {
        "name": "Crossbow, light",
        "equipped": True,
        "category": "Weapons"
    }
    
    enriched = _enrich_weapon_item(crossbow)
    print(f"Crossbow enriched: {enriched}")
    
    # Should have damage and range from builtin equipment
    assert enriched.get("damage"), f"Expected damage for Crossbow, got: {enriched}"
    assert enriched.get("damage_type"), f"Expected damage_type for Crossbow, got: {enriched}"
    assert enriched.get("range_text") or enriched.get("range"), f"Expected range for Crossbow, got: {enriched}"
    assert "1d8" in enriched.get("damage", ""), f"Expected 1d8 damage for Crossbow, got: {enriched.get('damage')}"
    assert "80/320" in (enriched.get("range_text") or enriched.get("range", "")), f"Expected 80/320 range for Crossbow, got: {enriched.get('range_text') or enriched.get('range')}"


def test_weapon_enrichment_with_rapier():
    """Test that Rapier enrichment returns damage and range."""
    rapier = {
        "name": "Rapier",
        "equipped": True,
        "category": "Weapons"
    }
    
    enriched = _enrich_weapon_item(rapier)
    print(f"Rapier enriched: {enriched}")
    
    # Should have damage from builtin equipment
    assert enriched.get("damage"), f"Expected damage for Rapier, got: {enriched}"
    assert enriched.get("damage_type"), f"Expected damage_type for Rapier, got: {enriched}"
    assert "1d8" in enriched.get("damage", ""), f"Expected 1d8 damage for Rapier, got: {enriched.get('damage')}"
    assert "piercing" in enriched.get("damage_type", ""), f"Expected piercing damage type, got: {enriched.get('damage_type')}"


def test_builtin_equipment_list_has_weapons():
    """Test that the builtin equipment list contains weapons."""
    weapons = _get_builtin_equipment_list()
    print(f"Found {len(weapons)} items in builtin equipment list")
    
    # Convert to dicts
    weapon_dicts = [w.to_dict() if hasattr(w, 'to_dict') else w for w in weapons]
    
    # Find specific weapons
    dagger = next((w for w in weapon_dicts if "dagger" in w.get("name", "").lower()), None)
    rapier = next((w for w in weapon_dicts if "rapier" in w.get("name", "").lower()), None)
    crossbow = next((w for w in weapon_dicts if "crossbow" in w.get("name", "").lower()), None)
    
    print(f"Dagger in list: {dagger is not None}")
    print(f"Rapier in list: {rapier is not None}")
    print(f"Crossbow in list: {crossbow is not None}")
    
    assert dagger, f"Dagger not found in builtin equipment. Available: {[w.get('name') for w in weapon_dicts[:5]]}"
    assert rapier, f"Rapier not found in builtin equipment"
    assert crossbow, f"Crossbow not found in builtin equipment"
    
    # Check that they have the right properties
    assert dagger.get("damage") == "1d4", f"Dagger damage: {dagger.get('damage')}"
    assert rapier.get("damage") == "1d8", f"Rapier damage: {rapier.get('damage')}"
    assert crossbow.get("damage") == "1d8", f"Crossbow damage: {crossbow.get('damage')}"


if __name__ == "__main__":
    test_builtin_equipment_list_has_weapons()
    test_weapon_enrichment_with_dagger()
    test_weapon_enrichment_with_crossbow()
    test_weapon_enrichment_with_rapier()
    print("\n✓ All tests passed!")
