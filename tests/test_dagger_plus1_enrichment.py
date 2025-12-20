import copy
import character


def test_dagger_and_dagger_plus1_enrichment():
    original = copy.deepcopy(character.EQUIPMENT_LIBRARY_STATE)
    try:
        # Ensure builtin list is present
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE["equipment"] = [itm for itm in [
            {'name':'Dagger','damage':'1d4','damage_type':'piercing','properties':'finesse, light'},
        ]]

        # Two items in inventory
        dagger = {'name':'Dagger','equipped':True,'category':'Weapons'}
        dagger_plus = {'name':'Dagger +1','equipped':True,'category':'Weapons'}

        enriched1 = character._enrich_weapon_item(dagger)
        enriched2 = character._enrich_weapon_item(dagger_plus)

        assert enriched1.get('damage') == '1d4'
        assert enriched2.get('damage') == '1d4'
    finally:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE.update(original)
