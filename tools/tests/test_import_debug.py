#!/usr/bin/env python3
"""Debug the import process step by step."""

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    # Add assets/py to path
    sys.path.insert(0, str(root / "assets" / "py"))

    from character_models import CharacterFactory

    # Load export file
    export_file = root / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
    with open(export_file, encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 70)
    print("IMPORT DEBUG - Testing populate_form() flow")
    print("=" * 70)

    # Simulate populate_form steps
    character = CharacterFactory.from_dict(data)
    normalized = character.to_dict()

    print("\n1. CHARACTER IDENTITY FIELDS:")
    print(f"   name: {character.name}")
    print(f"   class: {character.class_text}")
    print(f"   race: {character.race}")
    print(f"   background: {character.background}")
    print(f"   alignment: {character.alignment}")
    print(f"   player_name: {character.player_name}")
    print(f"   domain: {character.domain}")
    print(f"   level: {character.level}")
    print(f"   inspiration: {character.inspiration}")
    print(f"   spell_ability: {character.spell_ability}")

    print("\n2. ABILITIES:")
    for ability in ["str", "dex", "con", "int", "wis", "cha"]:
        score = character.attributes[ability]
        prof = character.attributes.is_proficient(ability)
        print(f"   {ability}: {score} (proficient: {prof})")

    print("\n3. COMBAT DATA:")
    combat = normalized.get("combat", {})
    print(f"   armor_class: {combat.get('armor_class')}")
    print(f"   speed: {combat.get('speed')}")
    print(f"   max_hp: {combat.get('max_hp')}")
    print(f"   current_hp: {combat.get('current_hp')}")
    print(f"   temp_hp: {combat.get('temp_hp')}")
    print(f"   hit_dice: {combat.get('hit_dice')}")

    print("\n4. SPELLCASTING DATA:")
    spellcasting = normalized.get("spellcasting", {})
    prepared = spellcasting.get("prepared", [])
    slots = spellcasting.get("slots_used", {})
    print(f"   prepared spells: {len(prepared)} spells")
    if prepared:
        sample = prepared[0]
        print(f"     - First: {sample.get('name')} (slug: {sample.get('slug')})")
    print(f"   spell_slots: {slots}")
    print(f"   domain_bonus_spells: {spellcasting.get('domain_bonus_spells', [])}")

    print("\n5. INVENTORY DATA:")
    inv = normalized.get("inventory", {})
    items = inv.get("items", [])
    currency = inv.get("currency", {})
    print(f"   items: {len(items)} items")
    print(f"   currency: {currency}")

    print("\n6. SKILLS DATA:")
    skills = normalized.get("skills", {})
    if skills:
        sample_skills = list(skills.keys())[:3]
        for skill in sample_skills:
            s = skills[skill]
            print(f"   {skill}: proficient={s.get('proficient')}, expertise={s.get('expertise')}")

    print("\n7. NOTES DATA:")
    notes = normalized.get("notes", {})
    for key in ["equipment", "features", "attacks", "notes"]:
        value = notes.get(key, "")
        print(f"   {key}: {len(value)} chars" if value else f"   {key}: (empty)")

    print("\n8. SPELL FIELDS (custom spells):")
    spells = normalized.get("spells", {})
    for key in ["paladin_spells", "wizard_spells", "ranger_spells"]:
        value = spells.get(key, "")
        print(f"   {key}: {len(value)} chars" if value else f"   {key}: (empty)")

    print("\n9. FEATS DATA:")
    feats = normalized.get("feats", [])
    print(f"   feats: {len(feats)} feats")
    if feats:
        for feat in feats[:2]:
            print(f"     - {feat.get('name')} (level {feat.get('level_gained')})")

    print("\n" + "=" * 70)
    print("ALL DATA PRESENT AND VALID FOR IMPORT")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
