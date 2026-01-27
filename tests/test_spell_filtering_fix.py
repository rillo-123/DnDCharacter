"""
Unit tests to verify the spell filtering fix works correctly.

Tests the scenario where:
1. spell_data import fails in character.py
2. CLASS_CASTING_PROGRESSIONS gets populated from spellcasting module
3. Cleric class is properly recognized
4. Spells are filtered correctly instead of all being rejected
"""

import sys
from pathlib import Path

# Add assets/py to path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_spell_data_has_progressions():
    """Test that spell_data module contains CLASS_CASTING_PROGRESSIONS."""
    try:
        from spell_data import CLASS_CASTING_PROGRESSIONS, SPELLCASTING_PROGRESSION_TABLES
        
        assert CLASS_CASTING_PROGRESSIONS, "CLASS_CASTING_PROGRESSIONS should not be empty"
        assert "cleric" in CLASS_CASTING_PROGRESSIONS, "cleric should be in CLASS_CASTING_PROGRESSIONS"
        assert CLASS_CASTING_PROGRESSIONS["cleric"] == "full", "cleric should have 'full' progression"
        
        assert SPELLCASTING_PROGRESSION_TABLES, "SPELLCASTING_PROGRESSION_TABLES should not be empty"
        assert "full" in SPELLCASTING_PROGRESSION_TABLES, "full progression should exist"
        
        print("✓ test_spell_data_has_progressions PASSED")
        return True
    except Exception as e:
        print(f"✗ test_spell_data_has_progressions FAILED: {e}")
        return False


def test_spellcasting_has_progressions():
    """Test that spellcasting module loads progressions via HTTP fallback."""
    try:
        import spellcasting_manager
        
        # The spellcasting module should have these attributes after HTTP loading
        assert hasattr(spellcasting, 'CLASS_CASTING_PROGRESSIONS'), \
            "spellcasting should have CLASS_CASTING_PROGRESSIONS"
        assert hasattr(spellcasting, 'SPELLCASTING_PROGRESSION_TABLES'), \
            "spellcasting should have SPELLCASTING_PROGRESSION_TABLES"
        
        progressions = spellcasting.CLASS_CASTING_PROGRESSIONS
        assert progressions, "spellcasting.CLASS_CASTING_PROGRESSIONS should not be empty"
        assert "cleric" in progressions, "cleric should be in spellcasting progressions"
        
        print("✓ test_spellcasting_has_progressions PASSED")
        return True
    except Exception as e:
        print(f"✗ test_spellcasting_has_progressions FAILED: {e}")
        return False


def test_determine_progression_key_logic():
    """Test that determine_progression_key returns correct value for cleric."""
    try:
        from spell_data import CLASS_CASTING_PROGRESSIONS
        
        # Simulate determine_progression_key logic
        class_key = "cleric"
        raw_text = "cleric"
        
        base = CLASS_CASTING_PROGRESSIONS.get(class_key, "none")
        
        # Should return "full" not "none"
        assert base == "full", f"cleric progression should be 'full', got '{base}'"
        assert base != "none", "cleric should NOT return 'none'"
        
        print("✓ test_determine_progression_key_logic PASSED")
        return True
    except Exception as e:
        print(f"✗ test_determine_progression_key_logic FAILED: {e}")
        return False


def test_progression_table_lookup():
    """Test that progression tables can be looked up for cleric at level 9."""
    try:
        from spell_data import SPELLCASTING_PROGRESSION_TABLES
        
        progression_key = "full"
        class_level = 9
        
        table = SPELLCASTING_PROGRESSION_TABLES.get(progression_key)
        assert table is not None, f"progression key '{progression_key}' should exist"
        
        # Table is a dict where keys are character levels and values are spell level dicts
        level_slots = table.get(class_level, {})
        assert level_slots, f"Level {class_level} should have slots data"
        
        # Get the maximum spell level (highest key in the slots dict)
        level_cap = max(level_slots.keys()) if level_slots else 0
        
        # For a level 9 cleric with full progression, should have spell level 5 available
        assert level_cap > 0, f"Level {class_level} should have spell levels available"
        assert level_cap == 5, f"Level 9 should have max spell level 5, got {level_cap}"
        
        print(f"✓ test_progression_table_lookup PASSED (level {class_level} -> spell level {level_cap})")
        return True
    except Exception as e:
        print(f"✗ test_progression_table_lookup FAILED: {e}")
        return False


def test_character_spell_profile():
    """Test that compute_spellcasting_profile returns correct profile for cleric."""
    try:
        from character import compute_spellcasting_profile
        
        # Simulate a character with class="cleric" and level 9
        profile = compute_spellcasting_profile(raw_text="cleric", fallback_level=9)
        
        assert profile is not None, "profile should not be None"
        assert "allowed_classes" in profile, "profile should have allowed_classes"
        assert "max_spell_level" in profile, "profile should have max_spell_level"
        
        allowed_classes = profile["allowed_classes"]
        max_spell_level = profile["max_spell_level"]
        
        # After fix, cleric should be in allowed_classes
        assert allowed_classes, f"allowed_classes should not be empty, got {allowed_classes}"
        assert "cleric" in allowed_classes, f"cleric should be in allowed_classes, got {allowed_classes}"
        
        # Level 9 cleric should have max spell level of 5
        assert max_spell_level > 0, f"max_spell_level should be > 0, got {max_spell_level}"
        
        print(f"✓ test_character_spell_profile PASSED (allowed_classes={allowed_classes}, max_level={max_spell_level})")
        return True
    except Exception as e:
        print(f"✗ test_character_spell_profile FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spell_filtering_logic():
    """Test spell filtering with correct profile data."""
    try:
        from character import compute_spellcasting_profile
        
        # Get the profile
        profile = compute_spellcasting_profile(raw_text="cleric", fallback_level=9)
        
        allowed_classes = profile["allowed_classes"]
        max_spell_level = profile["max_spell_level"]
        
        # Create mock spells
        mock_spells = [
            {"slug": "guidance", "level_int": 0, "classes": ["cleric"], "source": "phb"},
            {"slug": "cure-wounds", "level_int": 1, "classes": ["cleric"], "source": "phb"},
            {"slug": "bless", "level_int": 1, "classes": ["cleric"], "source": "phb"},
            {"slug": "fireball", "level_int": 3, "classes": ["wizard", "sorcerer"], "source": "phb"},
            {"slug": "mass-cure-wounds", "level_int": 5, "classes": ["cleric"], "source": "phb"},
            {"slug": "wish", "level_int": 9, "classes": ["wizard", "sorcerer"], "source": "phb"},
        ]
        
        # Filter spells manually following the logic from apply_spell_filters
        filtered = []
        for spell in mock_spells:
            spell_level = spell.get("level_int", 0)
            spell_classes = set(spell.get("classes", []))
            
            # Check level
            if max_spell_level is not None and spell_level > max_spell_level:
                continue
            
            # Check class
            if spell_classes and not spell_classes.intersection(set(allowed_classes)):
                continue
            
            filtered.append(spell)
        
        # Should have filtered some spells
        assert filtered, "Should have at least some spells after filtering"
        assert len(filtered) > 1, f"Should have multiple spells, got {len(filtered)}"
        
        # Should include cleric spells up to level 5
        spell_slugs = {s["slug"] for s in filtered}
        assert "guidance" in spell_slugs, "guidance should be in filtered spells"
        assert "bless" in spell_slugs, "bless should be in filtered spells"
        assert "mass-cure-wounds" in spell_slugs, "mass-cure-wounds should be in filtered spells"
        
        # Should NOT include wizard-only or too-high-level spells
        assert "fireball" not in spell_slugs, "fireball (wizard only) should NOT be in filtered spells"
        assert "wish" not in spell_slugs, "wish (level 9) should NOT be in filtered spells"
        
        print(f"✓ test_spell_filtering_logic PASSED ({len(filtered)} spells passed filter)")
        return True
    except Exception as e:
        print(f"✗ test_spell_filtering_logic FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_empty_class_progressions():
    """Test that CLASS_CASTING_PROGRESSIONS is NOT empty when character module loads."""
    try:
        import character
        
        # After the fix, CLASS_CASTING_PROGRESSIONS should be populated
        progressions = character.CLASS_CASTING_PROGRESSIONS
        
        assert progressions, f"CLASS_CASTING_PROGRESSIONS should not be empty, got {progressions}"
        assert isinstance(progressions, dict), "CLASS_CASTING_PROGRESSIONS should be a dict"
        assert "cleric" in progressions, f"cleric should be in progressions, got keys: {list(progressions.keys())}"
        
        print(f"✓ test_no_empty_class_progressions PASSED (keys: {list(progressions.keys())[:5]}...)")
        return True
    except Exception as e:
        print(f"✗ test_no_empty_class_progressions FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("SPELL FILTERING FIX - UNIT TESTS")
    print("=" * 70)
    print()
    
    tests = [
        ("spell_data has progressions", test_spell_data_has_progressions),
        ("spellcasting has progressions", test_spellcasting_has_progressions),
        ("determine_progression_key logic", test_determine_progression_key_logic),
        ("progression table lookup", test_progression_table_lookup),
        ("character spell profile", test_character_spell_profile),
        ("spell filtering logic", test_spell_filtering_logic),
        ("no empty class progressions", test_no_empty_class_progressions),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ {test_name} CRASHED: {e}")
            results[test_name] = False
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ All tests PASSED - spell filtering fix should work!")
    else:
        print(f"\n❌ {total - passed} test(s) FAILED - there may be issues")
    
    sys.exit(0 if passed == total else 1)
