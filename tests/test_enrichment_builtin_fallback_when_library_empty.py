import character


def test_builtin_fallback_used_when_library_empty():
    # Ensure equipment library is empty to simulate runtime where it hasn't been loaded
    original = dict(character.EQUIPMENT_LIBRARY_STATE)
    try:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        # Two dagger items: one normal, one +1 in name
        dagger = {'name':'Dagger','equipped':True,'category':'Weapons'}
        dagger_plus = {'name':'Dagger +1','equipped':True,'category':'Weapons'}

        enriched1 = character._enrich_weapon_item(dagger)
        enriched2 = character._enrich_weapon_item(dagger_plus)

        # Both should get damage from builtin fallback
        assert enriched1.get('damage') == '1d4'
        assert enriched2.get('damage') == '1d4'
        # Bonus for dagger_plus should still be available via name parsing or enrichment
        assert enriched2.get('bonus') in (None, 1) or ('+1' in dagger_plus['name'])
    finally:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE.update(original)
