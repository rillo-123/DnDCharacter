"""Unit tests for local equipment chooser data and filtering."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


EQUIPMENT_FILE = Path(__file__).parent.parent / "static" / "assets" / "data" / "equipment.json"


def load_equipment_sections() -> dict[str, list[dict]]:
    data = json.loads(EQUIPMENT_FILE.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if isinstance(value, list)}


def all_equipment_items() -> list[dict]:
    items: list[dict] = []
    for section, records in load_equipment_sections().items():
        for record in records:
            items.append({**record, "section": section})
    return items


class TestLocalEquipmentData(unittest.TestCase):
    """Test local equipment data used by the native JavaScript chooser."""

    def test_weapons_are_available(self):
        weapons = load_equipment_sections().get("weapons", [])

        self.assertGreater(len(weapons), 0)
        first_weapon = weapons[0]
        self.assertIn("name", first_weapon)
        self.assertIn("damage", first_weapon)
        self.assertIn("cost", first_weapon)

    def test_armor_is_available(self):
        armor = load_equipment_sections().get("armor", [])

        self.assertGreater(len(armor), 0)
        first_armor = armor[0]
        self.assertIn("name", first_armor)
        self.assertIn("cost", first_armor)
        self.assertIn("ac", first_armor)

    def test_mace_exists(self):
        names = [item["name"] for item in all_equipment_items()]

        self.assertIn("Mace", names, "Mace should be in the local equipment list")

    def test_total_equipment_count(self):
        self.assertGreaterEqual(len(all_equipment_items()), 20)


class TestEquipmentParsing(unittest.TestCase):
    """Test parsing of equipment cost and weight strings."""

    def test_parse_cost_gp(self):
        cost_str = "5 gp"
        match = re.search(r"(\d+(?:\.\d+)?)", cost_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 5.0)

    def test_parse_weight_lb(self):
        weight_str = "4 lb."
        match = re.search(r"(\d+(?:\.\d+)?)", weight_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 4.0)

    def test_parse_decimal_cost(self):
        cost_str = "0.5 gp"
        match = re.search(r"(\d+(?:\.\d+)?)", cost_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 0.5)

    def test_parse_unknown_cost(self):
        cost_str = "Unknown"
        match = re.search(r"(\d+(?:\.\d+)?)", cost_str)
        self.assertIsNone(match)

    def test_parse_multiple_numbers(self):
        cost_str = "50 gp or 100 sp"
        match = re.search(r"(\d+(?:\.\d+)?)", cost_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 50.0)


class TestEquipmentSearch(unittest.TestCase):
    """Test equipment search filtering."""

    def setUp(self):
        self.all_items = all_equipment_items()

    def search_items(self, search_term):
        return [item for item in self.all_items if search_term.lower() in item["name"].lower()]

    def test_search_mace(self):
        results = self.search_items("mace")
        self.assertGreater(len(results), 0)
        self.assertIn("Mace", [r["name"] for r in results])

    def test_search_sword(self):
        results = self.search_items("sword")
        self.assertGreater(len(results), 0)

    def test_search_armor_item(self):
        results = self.search_items("leather")
        self.assertGreater(len(results), 0)

    def test_search_case_insensitive(self):
        results_lower = self.search_items("mace")
        results_upper = self.search_items("MACE")
        self.assertEqual(len(results_lower), len(results_upper))

    def test_search_partial_match(self):
        results = self.search_items("lon")
        self.assertGreater(len(results), 0)
        names = [r["name"] for r in results]
        self.assertTrue(any("Longsword" in name for name in names))

    def test_search_no_results(self):
        results = self.search_items("xyz_nonexistent")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
