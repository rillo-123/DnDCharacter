"""
GUI Interaction Tests for DnDCharacter (PySheet)

Covers all client-side interaction wiring:
  - Tab navigation (pure JavaScript, no PyScript required)
  - HTML element presence and data-attribute wiring for every interactive element
  - Custom item modal open/close (pure JavaScript cancel/close handlers)
  - data-character-input autosave attribute coverage
  - Backend API endpoints (/api/export, /api/exports, /api/console-log)

Note: Tests that require the PyScript WASM runtime (ability score modifier
calculations, equipment library loading, spell preparation, character
save/load via localStorage) are covered by the existing Python unit-test
suite in this same /tests/ directory and are intentionally excluded here.
"""

import re
import subprocess
import time
from pathlib import Path

import pytest
import requests as req
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Server configuration
# ---------------------------------------------------------------------------

_PORT = 8765
_BASE_URL = f"http://127.0.0.1:{_PORT}"

# ---------------------------------------------------------------------------
# Session-level fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def flask_server():
    """Start the Flask backend once for the whole test session."""
    repo_root = Path(__file__).parent.parent
    proc = subprocess.Popen(
        ["python3", "backend.py", "--host", "127.0.0.1", f"--port={_PORT}"],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait up to 10 s for the server to become reachable
    for _ in range(20):
        try:
            req.get(f"{_BASE_URL}/", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    yield _BASE_URL
    proc.terminate()
    proc.wait(timeout=5)


# ---------------------------------------------------------------------------
# Page fixtures (function-scoped – each test gets a fresh page)
# ---------------------------------------------------------------------------


@pytest.fixture()
def app_page(page: Page, flask_server):
    """Navigate to the app root and wait for the DOM."""
    page.goto(flask_server + "/")
    page.wait_for_load_state("domcontentloaded")
    return page


@pytest.fixture()
def inventory_page(app_page: Page):
    app_page.click('[data-tab="inventory"]')
    return app_page


@pytest.fixture()
def skills_page(app_page: Page):
    app_page.click('[data-tab="skills"]')
    return app_page


@pytest.fixture()
def combat_page(app_page: Page):
    app_page.click('[data-tab="combat"]')
    return app_page


@pytest.fixture()
def spells_page(app_page: Page):
    app_page.click('[data-tab="spells"]')
    return app_page


@pytest.fixture()
def feats_page(app_page: Page):
    app_page.click('[data-tab="feats"]')
    return app_page


@pytest.fixture()
def manage_page(app_page: Page):
    app_page.click('[data-tab="manage"]')
    return app_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_TABS = ["overview", "inventory", "skills", "combat", "spells", "feats", "manage"]

_ALL_SKILLS = [
    "acrobatics", "animal_handling", "arcana", "athletics", "deception",
    "history", "insight", "intimidation", "investigation", "medicine",
    "nature", "perception", "performance", "persuasion", "religion",
    "sleight_of_hand", "stealth", "survival",
]

_ABILITIES = ["str", "dex", "con", "int", "wis", "cha"]

_CURRENCIES = ["pp", "gp", "ep", "sp", "cp"]
# (data-amount value, expected button text)
_CURRENCY_DELTAS = [("-100", "-100"), ("-10", "-10"), ("10", "+10"), ("100", "+100")]

# (data-adjust-delta, data-adjust-target)
_HP_BUTTONS = [
    ("-10", "current_hp"), ("-5", "current_hp"), ("-1", "current_hp"),
    ("1",  "current_hp"), ("5",  "current_hp"), ("10", "current_hp"),
]
_TEMP_HP_BUTTONS = [("1", "temp_hp"), ("5", "temp_hp")]
_HIT_DICE_BUTTONS = [("-1", "hit_dice_available"), ("1", "hit_dice_available")]

_AUTOSAVE_FIELDS = [
    "#name", "#class", "#race", "#background", "#subclass", "#alignment",
    "#player_name", "#level",
    "#str-score", "#dex-score", "#con-score", "#int-score", "#wis-score", "#cha-score",
    "#str-save-prof", "#dex-save-prof", "#con-save-prof",
    "#int-save-prof", "#wis-save-prof", "#cha-save-prof",
    "#speed", "#max_hp",
    "#death_saves_success_1", "#death_saves_success_2", "#death_saves_success_3",
    "#death_saves_failure_1", "#death_saves_failure_2", "#death_saves_failure_3",
]


def _has_class(page: Page, selector: str, cls: str) -> bool:
    classes = (page.locator(selector).get_attribute("class") or "").split()
    return cls in classes


# ===========================================================================
# 1. Page Load
# ===========================================================================

class TestPageLoad:

    def test_page_title(self, app_page):
        expect(app_page).to_have_title("PySheet · D&D 5e Character Sheet")

    def test_seven_tab_buttons_present(self, app_page):
        expect(app_page.locator(".tab")).to_have_count(7)

    def test_tab_labels(self, app_page):
        for tab in _ALL_TABS:
            btn = app_page.locator(f'[data-tab="{tab}"]')
            expect(btn).to_be_attached()
            expect(btn).to_have_text(tab.capitalize())

    def test_overview_tab_active_by_default(self, app_page):
        assert _has_class(app_page, '[data-tab="overview"]', "active")

    def test_overview_panel_visible_by_default(self, app_page):
        expect(app_page.locator("#tab-overview")).to_be_visible()

    def test_other_panels_hidden_by_default(self, app_page):
        for tab in _ALL_TABS[1:]:
            expect(app_page.locator(f"#tab-{tab}")).to_be_hidden()

    def test_character_header_name_present(self, app_page):
        expect(app_page.locator("#character-header-name")).to_be_visible()

    def test_character_header_summary_present(self, app_page):
        expect(app_page.locator("#character-header-summary")).to_be_visible()

    def test_saving_indicator_present(self, app_page):
        expect(app_page.locator("#saving-indicator")).to_be_attached()

    def test_saving_lamp_present(self, app_page):
        expect(app_page.locator(".saving-lamp")).to_be_attached()


# ===========================================================================
# 2. Tab Navigation (pure JavaScript)
# ===========================================================================

class TestTabNavigation:

    @pytest.mark.parametrize("tab", _ALL_TABS)
    def test_clicking_tab_shows_its_panel(self, app_page, tab):
        app_page.click(f'[data-tab="{tab}"]')
        expect(app_page.locator(f"#tab-{tab}")).to_be_visible()

    @pytest.mark.parametrize("tab", _ALL_TABS)
    def test_clicking_tab_marks_button_active(self, app_page, tab):
        app_page.click(f'[data-tab="{tab}"]')
        assert _has_class(app_page, f'[data-tab="{tab}"]', "active")

    @pytest.mark.parametrize("tab", _ALL_TABS)
    def test_clicking_tab_hides_all_other_panels(self, app_page, tab):
        app_page.click(f'[data-tab="{tab}"]')
        for other in _ALL_TABS:
            if other != tab:
                expect(app_page.locator(f"#tab-{other}")).to_be_hidden()

    @pytest.mark.parametrize("tab", _ALL_TABS)
    def test_clicking_tab_deactivates_all_other_buttons(self, app_page, tab):
        app_page.click(f'[data-tab="{tab}"]')
        for other in _ALL_TABS:
            if other != tab:
                assert not _has_class(app_page, f'[data-tab="{other}"]', "active"), \
                    f"Button [{other}] should not be active when [{tab}] is selected"

    def test_full_round_trip_through_all_tabs(self, app_page):
        for tab in _ALL_TABS:
            app_page.click(f'[data-tab="{tab}"]')
            expect(app_page.locator(f"#tab-{tab}")).to_be_visible()

    def test_switching_back_to_previous_tab(self, app_page):
        app_page.click('[data-tab="combat"]')
        expect(app_page.locator("#tab-combat")).to_be_visible()
        app_page.click('[data-tab="overview"]')
        expect(app_page.locator("#tab-overview")).to_be_visible()
        expect(app_page.locator("#tab-combat")).to_be_hidden()

    def test_only_one_panel_visible_at_a_time(self, app_page):
        app_page.click('[data-tab="spells"]')
        visible = [
            tab for tab in _ALL_TABS
            if app_page.locator(f"#tab-{tab}").is_visible()
        ]
        assert visible == ["spells"], f"Expected only 'spells' panel visible, got {visible}"

    def test_only_one_button_active_at_a_time(self, app_page):
        app_page.click('[data-tab="feats"]')
        active = [
            tab for tab in _ALL_TABS
            if _has_class(app_page, f'[data-tab="{tab}"]', "active")
        ]
        assert active == ["feats"], f"Expected only 'feats' button active, got {active}"


# ===========================================================================
# 3. Overview Tab – Structure & Input Wiring
# ===========================================================================

class TestOverviewTab:

    def test_character_name_input_present(self, app_page):
        expect(app_page.locator("#name")).to_be_attached()

    def test_character_name_has_autosave_attr(self, app_page):
        assert app_page.locator("#name").get_attribute("data-character-input") is not None

    def test_character_name_default_placeholder(self, app_page):
        assert app_page.locator("#name").get_attribute("placeholder") is not None

    def test_class_select_present(self, app_page):
        expect(app_page.locator("#class")).to_be_attached()

    def test_class_select_has_expected_classes(self, app_page):
        expected = [
            "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
            "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
        ]
        options = app_page.locator("#class option").all_text_contents()
        for cls in expected:
            assert cls in options, f"Class '{cls}' missing from #class select"

    def test_race_select_present_with_options(self, app_page):
        expect(app_page.locator("#race")).to_be_attached()
        count = app_page.locator("#race option").count()
        assert count > 5, "Race select should have more than 5 options"

    def test_background_select_present_with_options(self, app_page):
        expect(app_page.locator("#background")).to_be_attached()
        count = app_page.locator("#background option").count()
        assert count > 5, "Background select should have more than 5 options"

    def test_subclass_select_present(self, app_page):
        expect(app_page.locator("#subclass")).to_be_attached()

    def test_subclass_row_hidden_by_default(self, app_page):
        """Row must be hidden on page load (default class is not Cleric or Bard)."""
        row = app_page.locator("[data-subclass-row]")
        expect(row).to_be_attached()
        display = app_page.evaluate(
            "document.querySelector('[data-subclass-row]').style.display"
        )
        assert display == "none", (
            f"[data-subclass-row] should be hidden by default, got display='{display}'"
        )

    def test_subclass_row_has_label_element(self, app_page):
        expect(app_page.locator("#subclass-label")).to_be_attached()

    def test_subclass_row_has_cleric_domain_options(self, app_page):
        options = app_page.locator('#subclass option[data-class="cleric"]').all_text_contents()
        assert len(options) > 0, "Subclass select must contain Cleric domain options"

    def test_subclass_row_has_bard_college_options(self, app_page):
        options = app_page.locator('#subclass option[data-class="bard"]').all_text_contents()
        assert len(options) > 0, "Subclass select must contain Bard college options"

    def test_alignment_select_present(self, app_page):
        alignments = app_page.locator("#alignment option").all_text_contents()
        assert "Lawful Good" in alignments
        assert "Chaotic Evil" in alignments

    def test_player_name_input_present(self, app_page):
        expect(app_page.locator("#player_name")).to_be_attached()

    def test_level_input_is_number_type(self, app_page):
        assert app_page.locator("#level").get_attribute("type") == "number"

    def test_level_input_range_1_to_20(self, app_page):
        assert app_page.locator("#level").get_attribute("min") == "1"
        assert app_page.locator("#level").get_attribute("max") == "20"

    def test_level_default_value_1(self, app_page):
        assert app_page.locator("#level").input_value() == "1"

    def test_proficiency_bonus_output_present(self, app_page):
        expect(app_page.locator("#proficiency-bonus")).to_be_attached()

    def test_proficiency_bonus_default_plus_2(self, app_page):
        expect(app_page.locator("#proficiency-bonus")).to_have_text("+2")

    @pytest.mark.parametrize("ability", _ABILITIES)
    def test_ability_score_input_present(self, app_page, ability):
        expect(app_page.locator(f"#{ability}-score")).to_be_attached()

    @pytest.mark.parametrize("ability", _ABILITIES)
    def test_ability_score_default_10(self, app_page, ability):
        assert app_page.locator(f"#{ability}-score").input_value() == "10"

    @pytest.mark.parametrize("ability", _ABILITIES)
    def test_ability_score_range_1_to_30(self, app_page, ability):
        el = app_page.locator(f"#{ability}-score")
        assert el.get_attribute("min") == "1"
        assert el.get_attribute("max") == "30"

    @pytest.mark.parametrize("ability", _ABILITIES)
    def test_ability_save_prof_checkbox_present(self, app_page, ability):
        expect(app_page.locator(f"#{ability}-save-prof")).to_be_attached()

    @pytest.mark.parametrize("ability", _ABILITIES)
    def test_ability_row_data_attribute(self, app_page, ability):
        expect(app_page.locator(f'.ability-row[data-ability="{ability}"]')).to_be_attached()


# ===========================================================================
# 4. Inventory Tab – Structure & Currency Button Wiring
# ===========================================================================

class TestInventoryTab:

    def test_equipment_load_btn_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-load-btn")).to_be_attached()

    def test_equipment_load_btn_has_py_click(self, inventory_page):
        assert inventory_page.locator("#equipment-load-btn").get_attribute("py-click") == \
            "load_equipment_library"

    def test_equipment_add_btn_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-add-btn")).to_be_attached()

    def test_equipment_custom_btn_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-custom-btn")).to_be_attached()

    def test_equipment_search_input_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-search-input")).to_be_attached()

    def test_equipment_table_container_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-table")).to_be_attached()

    def test_equipment_total_weight_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-total-weight")).to_be_attached()
        expect(inventory_page.locator("#equipment-total-weight")).to_have_text("0")

    def test_equipment_total_cost_present(self, inventory_page):
        expect(inventory_page.locator("#equipment-total-cost")).to_be_attached()
        expect(inventory_page.locator("#equipment-total-cost")).to_have_text("0")

    @pytest.mark.parametrize("currency", _CURRENCIES)
    def test_currency_input_present(self, inventory_page, currency):
        expect(inventory_page.locator(f"#currency-{currency}")).to_be_attached()

    @pytest.mark.parametrize("currency", _CURRENCIES)
    def test_currency_input_default_zero(self, inventory_page, currency):
        assert inventory_page.locator(f"#currency-{currency}").input_value() == "0"

    @pytest.mark.parametrize("currency", _CURRENCIES)
    def test_currency_input_has_autosave_attr(self, inventory_page, currency):
        assert inventory_page.locator(f"#currency-{currency}").get_attribute(
            "data-character-input"
        ) is not None

    @pytest.mark.parametrize("currency", _CURRENCIES)
    def test_currency_input_has_currency_field_attr(self, inventory_page, currency):
        assert inventory_page.locator(f"#currency-{currency}").get_attribute(
            "data-currency-field"
        ) == currency

    @pytest.mark.parametrize("currency,amount,label", [
        (c, a, l)
        for c in _CURRENCIES
        for a, l in _CURRENCY_DELTAS
    ])
    def test_currency_button_data_attributes(self, inventory_page, currency, amount, label):
        btn = inventory_page.locator(f'[data-currency="{currency}"][data-amount="{amount}"]')
        expect(btn).to_be_attached()
        expect(btn).to_have_text(label)

    def test_total_currency_buttons_count(self, inventory_page):
        # 5 currencies × 4 buttons = 20
        expect(inventory_page.locator(".currency-btn")).to_have_count(20)


# ===========================================================================
# 5. Skills Tab – Structure & Data-Attribute Wiring
# ===========================================================================

class TestSkillsTab:

    def test_exactly_18_skill_rows(self, skills_page):
        expect(skills_page.locator("[data-skill]")).to_have_count(18)

    @pytest.mark.parametrize("skill", _ALL_SKILLS)
    def test_skill_row_data_attribute_present(self, skills_page, skill):
        expect(skills_page.locator(f'[data-skill="{skill}"]')).to_be_attached()

    @pytest.mark.parametrize("skill", _ALL_SKILLS)
    def test_skill_proficiency_checkbox_present(self, skills_page, skill):
        expect(skills_page.locator(f"#{skill}-prof")).to_be_attached()

    @pytest.mark.parametrize("skill", _ALL_SKILLS)
    def test_skill_expertise_checkbox_present(self, skills_page, skill):
        expect(skills_page.locator(f"#{skill}-exp")).to_be_attached()

    @pytest.mark.parametrize("skill", _ALL_SKILLS)
    def test_skill_total_output_present(self, skills_page, skill):
        expect(skills_page.locator(f"#{skill}-total")).to_be_attached()

    @pytest.mark.parametrize("skill", _ALL_SKILLS)
    def test_skill_default_total_is_plus_zero(self, skills_page, skill):
        text = skills_page.locator(f"#{skill}-total").text_content()
        assert text is not None and text.strip() == "+0", \
            f"Skill '{skill}' default total should be '+0', got '{text}'"

    def test_passive_perception_element_present(self, skills_page):
        expect(skills_page.locator("#passive-perception")).to_be_attached()

    def test_passive_perception_default_10(self, skills_page):
        text = skills_page.locator("#passive-perception").text_content()
        assert text is not None and text.strip() == "10"

    def test_weapons_grid_present(self, skills_page):
        expect(skills_page.locator("#weapons-grid")).to_be_attached()

    def test_armor_grid_present(self, skills_page):
        expect(skills_page.locator("#armor-grid")).to_be_attached()


# ===========================================================================
# 6. Combat Tab – Structure & HP/Adjust Button Wiring
# ===========================================================================

class TestCombatTab:

    # --- read-only stat displays ---

    def test_total_armor_class_present(self, combat_page):
        expect(combat_page.locator("#total_armor_class")).to_be_attached()

    def test_total_armor_class_default_10(self, combat_page):
        expect(combat_page.locator("#total_armor_class")).to_have_text("10")

    def test_initiative_present(self, combat_page):
        expect(combat_page.locator("#initiative")).to_be_attached()

    def test_initiative_default_plus_zero(self, combat_page):
        expect(combat_page.locator("#initiative")).to_have_text("+0")

    def test_hit_dice_display_present(self, combat_page):
        expect(combat_page.locator("#hit_dice")).to_be_attached()

    def test_hit_dice_default_1d8(self, combat_page):
        expect(combat_page.locator("#hit_dice")).to_have_text("1d8")

    def test_concentration_save_present(self, combat_page):
        expect(combat_page.locator("#concentration-save")).to_be_attached()

    def test_spell_save_dc_present(self, combat_page):
        expect(combat_page.locator("#spell-save-dc")).to_be_attached()

    def test_spell_save_dc_default_8(self, combat_page):
        expect(combat_page.locator("#spell-save-dc")).to_have_text("8")

    def test_spell_attack_bonus_present(self, combat_page):
        expect(combat_page.locator("#spell-attack")).to_be_attached()

    def test_spell_attack_default_plus_zero(self, combat_page):
        expect(combat_page.locator("#spell-attack")).to_have_text("+0")

    # --- editable inputs ---

    def test_speed_input_present(self, combat_page):
        expect(combat_page.locator("#speed")).to_be_attached()

    def test_speed_default_30(self, combat_page):
        assert combat_page.locator("#speed").input_value() == "30"

    def test_max_hp_input_present(self, combat_page):
        expect(combat_page.locator("#max_hp")).to_be_attached()

    def test_max_hp_default_8(self, combat_page):
        assert combat_page.locator("#max_hp").input_value() == "8"

    def test_current_hp_hidden_input_present(self, combat_page):
        hp = combat_page.locator("#current_hp")
        expect(hp).to_be_attached()
        assert hp.get_attribute("type") == "hidden"

    def test_temp_hp_hidden_input_present(self, combat_page):
        tmp = combat_page.locator("#temp_hp")
        expect(tmp).to_be_attached()
        assert tmp.get_attribute("type") == "hidden"

    def test_hit_dice_available_hidden_input_present(self, combat_page):
        hd = combat_page.locator("#hit_dice_available")
        expect(hd).to_be_attached()
        assert hd.get_attribute("type") == "hidden"

    # --- death saves ---

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_death_save_success_checkbox_present(self, combat_page, n):
        expect(combat_page.locator(f"#death_saves_success_{n}")).to_be_attached()

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_death_save_failure_checkbox_present(self, combat_page, n):
        expect(combat_page.locator(f"#death_saves_failure_{n}")).to_be_attached()

    # --- HP adjustment button data-attribute wiring ---

    @pytest.mark.parametrize("delta,target", _HP_BUTTONS)
    def test_hp_button_data_adjust_attributes(self, combat_page, delta, target):
        btn = combat_page.locator(
            f'[data-adjust-target="{target}"][data-adjust-delta="{delta}"]'
        )
        expect(btn).to_be_attached()

    @pytest.mark.parametrize("delta,_", _HP_BUTTONS)
    def test_hp_buttons_clamp_at_zero_min(self, combat_page, delta, _):
        btn = combat_page.locator(
            f'[data-adjust-target="current_hp"][data-adjust-delta="{delta}"]'
        )
        assert btn.get_attribute("data-adjust-min") == "0"

    @pytest.mark.parametrize("delta,_", _HP_BUTTONS)
    def test_hp_buttons_are_capped_by_max_hp(self, combat_page, delta, _):
        btn = combat_page.locator(
            f'[data-adjust-target="current_hp"][data-adjust-delta="{delta}"]'
        )
        assert btn.get_attribute("data-adjust-max-id") == "max_hp"

    def test_set_to_max_button_wiring(self, combat_page):
        btn = combat_page.locator(
            '[data-adjust-target="current_hp"][data-adjust-set-id="max_hp"]'
        )
        expect(btn).to_be_attached()
        expect(btn).to_have_text("Set to Max")

    # --- Temp HP button wiring ---

    @pytest.mark.parametrize("delta,target", _TEMP_HP_BUTTONS)
    def test_temp_hp_button_data_attributes(self, combat_page, delta, target):
        btn = combat_page.locator(
            f'[data-adjust-target="{target}"][data-adjust-delta="{delta}"]'
        )
        expect(btn).to_be_attached()

    def test_clear_temp_hp_button_wiring(self, combat_page):
        btn = combat_page.locator('[data-adjust-target="temp_hp"][data-adjust-set="0"]')
        expect(btn).to_be_attached()
        expect(btn).to_have_text("Clear Temp")

    # --- Hit dice button wiring ---

    @pytest.mark.parametrize("delta,target", _HIT_DICE_BUTTONS)
    def test_hit_dice_button_data_attributes(self, combat_page, delta, target):
        btn = combat_page.locator(
            f'[data-adjust-target="{target}"][data-adjust-delta="{delta}"]'
        )
        expect(btn).to_be_attached()

    def test_refill_hit_dice_button_wiring(self, combat_page):
        btn = combat_page.locator(
            '[data-adjust-target="hit_dice_available"][data-adjust-set-id="level"]'
        )
        expect(btn).to_be_attached()
        expect(btn).to_have_text("Refill to Level")

    # --- Channel Divinity button wiring ---

    def test_channel_divinity_use_button_wiring(self, combat_page):
        btn = combat_page.locator(
            '[data-adjust-target="channel_divinity_available"][data-adjust-delta="-1"]'
        )
        expect(btn).to_be_attached()
        expect(btn).to_have_text("Use 1")


# ===========================================================================
# 7. Spells Tab – Structure
# ===========================================================================

class TestSpellsTab:

    def test_load_spells_button_present(self, spells_page):
        expect(spells_page.locator("#spells-load-btn")).to_be_attached()

    def test_load_spells_has_py_click(self, spells_page):
        attr = spells_page.locator("#spells-load-btn").get_attribute("py-click")
        assert attr is not None

    def test_long_rest_spell_button_present(self, spells_page):
        expect(spells_page.locator("#long-rest-spell-btn")).to_be_attached()

    def test_spell_search_input_present(self, spells_page):
        expect(spells_page.locator("#spell-search")).to_be_attached()

    def test_spell_level_filter_present(self, spells_page):
        expect(spells_page.locator("#spell-level-filter")).to_be_attached()

    def test_spell_level_filter_has_cantrip_option(self, spells_page):
        opts = spells_page.locator("#spell-level-filter option").all_text_contents()
        assert any("Cantrip" in o or "(0)" in o for o in opts), \
            "Spell level filter should include a Cantrip option"

    def test_spell_level_filter_has_options_1_through_9(self, spells_page):
        opts = spells_page.locator("#spell-level-filter option").all_text_contents()
        for lvl in range(1, 10):
            assert any(str(lvl) in o for o in opts), \
                f"Spell level filter should include Level {lvl}"

    def test_spell_class_filter_present(self, spells_page):
        expect(spells_page.locator("#spell-class-filter")).to_be_attached()

    def test_spell_library_status_message_present(self, spells_page):
        expect(spells_page.locator("#spell-library-status")).to_be_attached()

    def test_spell_library_results_container_present(self, spells_page):
        expect(spells_page.locator("#spell-library-results")).to_be_attached()

    def test_spellbook_prepared_count_present(self, spells_page):
        expect(spells_page.locator("#spellbook-prepared-count")).to_be_attached()

    def test_spellbook_prepared_count_default_0_of_0(self, spells_page):
        expect(spells_page.locator("#spellbook-prepared-count")).to_have_text("0 / 0")

    def test_spellbook_slots_summary_container_present(self, spells_page):
        expect(spells_page.locator("#spellbook-slots-summary")).to_be_attached()

    def test_spellbook_empty_state_present(self, spells_page):
        expect(spells_page.locator("#spellbook-empty-state")).to_be_attached()

    def test_spellbook_empty_state_mentions_spell_library(self, spells_page):
        text = spells_page.locator("#spellbook-empty-state").text_content() or ""
        assert "Spell Library" in text

    def test_spellbook_levels_container_present(self, spells_page):
        expect(spells_page.locator("#spellbook-levels")).to_be_attached()


# ===========================================================================
# 8. Feats Tab – Structure
# ===========================================================================

class TestFeatsTab:

    def test_class_features_container_present(self, feats_page):
        expect(feats_page.locator("#class-features-container")).to_be_attached()

    def test_feat_name_input_present(self, feats_page):
        expect(feats_page.locator("#feat-name-input")).to_be_attached()

    def test_feat_name_input_is_text(self, feats_page):
        assert feats_page.locator("#feat-name-input").get_attribute("type") in (None, "text")

    def test_feat_name_has_helpful_placeholder(self, feats_page):
        placeholder = feats_page.locator("#feat-name-input").get_attribute("placeholder") or ""
        assert len(placeholder) > 0, "feat-name-input should have a placeholder"

    def test_feat_level_input_is_number(self, feats_page):
        assert feats_page.locator("#feat-level-input").get_attribute("type") == "number"

    def test_feat_level_input_range_1_to_20(self, feats_page):
        el = feats_page.locator("#feat-level-input")
        assert el.get_attribute("min") == "1"
        assert el.get_attribute("max") == "20"

    def test_feat_level_default_1(self, feats_page):
        assert feats_page.locator("#feat-level-input").input_value() == "1"

    def test_feat_description_textarea_present(self, feats_page):
        expect(feats_page.locator("#feat-description-input")).to_be_attached()

    def test_feat_add_button_present_with_correct_label(self, feats_page):
        btn = feats_page.locator("#feat-add-btn")
        expect(btn).to_be_attached()
        expect(btn).to_have_text("Add Feat")

    def test_feat_add_button_has_py_click(self, feats_page):
        assert feats_page.locator("#feat-add-btn").get_attribute("py-click") == "add_feat"

    def test_feats_list_container_present(self, feats_page):
        expect(feats_page.locator("#feats-list")).to_be_attached()


# ===========================================================================
# 9. Manage Tab – Structure
# ===========================================================================

class TestManageTab:

    def test_character_switcher_select_present(self, manage_page):
        expect(manage_page.locator("#character-switcher")).to_be_attached()

    def test_long_rest_button_present(self, manage_page):
        expect(manage_page.locator("#long-rest-btn")).to_be_attached()

    def test_save_button_present_with_label(self, manage_page):
        expect(manage_page.locator("#save-btn")).to_have_text("Save to Browser")

    def test_reset_button_present_with_label(self, manage_page):
        expect(manage_page.locator("#reset-btn")).to_have_text("Reset")

    def test_export_button_present_with_label(self, manage_page):
        expect(manage_page.locator("#export-btn")).to_have_text("Export JSON")

    def test_import_file_input_present(self, manage_page):
        expect(manage_page.locator("#import-file")).to_be_attached()

    def test_import_file_accepts_json(self, manage_page):
        accept = manage_page.locator("#import-file").get_attribute("accept") or ""
        assert "json" in accept.lower(), f"import-file accept should mention json, got: {accept}"

    def test_storage_info_button_present(self, manage_page):
        expect(manage_page.locator("#storage-info-btn")).to_be_attached()

    def test_cleanup_button_present(self, manage_page):
        expect(manage_page.locator("#cleanup-btn")).to_be_attached()

    def test_storage_message_container_present(self, manage_page):
        expect(manage_page.locator("#storage-message")).to_be_attached()

    def test_save_button_has_py_click(self, manage_page):
        assert manage_page.locator("#save-btn").get_attribute("py-click") == "save_character"

    def test_reset_button_has_py_click(self, manage_page):
        assert manage_page.locator("#reset-btn").get_attribute("py-click") == "reset_character"

    def test_export_button_has_py_click(self, manage_page):
        assert manage_page.locator("#export-btn").get_attribute("py-click") is not None

    def test_storage_info_button_has_py_click(self, manage_page):
        assert manage_page.locator("#storage-info-btn").get_attribute("py-click") is not None


# ===========================================================================
# 10. Custom Item Modal – Pure JavaScript close handlers
# ===========================================================================

class TestCustomItemModal:

    def test_modal_exists_in_dom(self, inventory_page):
        expect(inventory_page.locator("#custom-item-modal")).to_be_attached()

    def test_modal_hidden_on_page_load(self, inventory_page):
        display = inventory_page.evaluate(
            "document.getElementById('custom-item-modal').style.display"
        )
        assert display == "none", f"Modal should start hidden, got display='{display}'"

    def test_add_item_button_inside_modal_present(self, inventory_page):
        expect(inventory_page.locator("#custom-item-add")).to_be_attached()
        expect(inventory_page.locator("#custom-item-add")).to_have_text("Add Item")

    def test_cancel_button_inside_modal_present(self, inventory_page):
        expect(inventory_page.locator("#custom-item-cancel")).to_be_attached()
        expect(inventory_page.locator("#custom-item-cancel")).to_have_text("Cancel")

    def test_close_x_button_inside_modal_present(self, inventory_page):
        expect(inventory_page.locator("#custom-item-close")).to_be_attached()

    def test_cancel_button_closes_modal(self, inventory_page):
        # Open via JS (bypasses the PyScript py-click dependency)
        inventory_page.evaluate(
            "document.getElementById('custom-item-modal').style.display = 'block'"
        )
        inventory_page.click("#custom-item-cancel")
        display = inventory_page.evaluate(
            "document.getElementById('custom-item-modal').style.display"
        )
        assert display == "none", f"Cancel should hide modal, got display='{display}'"

    def test_close_x_button_closes_modal(self, inventory_page):
        inventory_page.evaluate(
            "document.getElementById('custom-item-modal').style.display = 'block'"
        )
        inventory_page.click("#custom-item-close")
        display = inventory_page.evaluate(
            "document.getElementById('custom-item-modal').style.display"
        )
        assert display == "none", f"Close X should hide modal, got display='{display}'"

    def test_modal_can_be_shown_and_hidden_repeatedly(self, inventory_page):
        for _ in range(3):
            inventory_page.evaluate(
                "document.getElementById('custom-item-modal').style.display = 'block'"
            )
            inventory_page.click("#custom-item-cancel")
            display = inventory_page.evaluate(
                "document.getElementById('custom-item-modal').style.display"
            )
            assert display == "none"


# ===========================================================================
# 11. data-character-input Autosave Attribute Wiring
# ===========================================================================

class TestAutosaveWiring:

    @pytest.mark.parametrize("selector", _AUTOSAVE_FIELDS)
    def test_field_has_data_character_input(self, app_page, selector):
        el = app_page.locator(selector)
        assert el.get_attribute("data-character-input") is not None, \
            f"{selector} is missing the data-character-input autosave attribute"

    def test_minimum_autosave_field_count(self, app_page):
        count = app_page.locator("[data-character-input]").count()
        assert count >= 30, \
            f"Expected at least 30 data-character-input fields across the page, got {count}"


# ===========================================================================
# 12. API: POST /api/export
# ===========================================================================

class TestAPIExport:

    def test_valid_export_returns_200(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": "APITest_Fighter_lvl1_valid.json", "content": {"name": "APITest"}},
        )
        assert resp.status_code == 200

    def test_valid_export_success_true(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": "APITest_Fighter_lvl1_success.json", "content": {"name": "APITest"}},
        )
        assert resp.json()["success"] is True

    def test_export_response_contains_filename(self, flask_server):
        fname = "APITest_Rogue_lvl3_fname.json"
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": fname, "content": {"name": "APITest"}},
        )
        assert resp.json()["filename"] == fname

    def test_export_response_contains_size(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": "APITest_Bard_lvl2_size.json", "content": {"name": "APITest"}},
        )
        assert resp.json()["size"] > 0

    def test_export_file_written_to_disk(self, flask_server):
        fname = "APITest_Wizard_lvl5_disk.json"
        req.post(
            f"{flask_server}/api/export",
            json={"filename": fname, "content": {"name": "DiskCheck", "level": 5}},
        )
        repo = Path(__file__).parent.parent
        found = any((d / fname).exists() for d in [
            repo / "exports" / "autosaves",
            repo / "exports",
        ])
        assert found, f"Export file '{fname}' was not found on disk"

    def test_export_file_content_is_valid_json(self, flask_server):
        fname = "APITest_Druid_lvl4_json.json"
        payload = {"name": "DruidTest", "level": 4, "spells": ["Healing Word"]}
        req.post(f"{flask_server}/api/export", json={"filename": fname, "content": payload})
        repo = Path(__file__).parent.parent
        for d in [repo / "exports" / "autosaves", repo / "exports"]:
            candidate = d / fname
            if candidate.exists():
                import json
                data = json.loads(candidate.read_text())
                assert data["name"] == "DruidTest"
                assert data["level"] == 4
                return
        pytest.fail(f"Export file '{fname}' not found for content verification")

    def test_missing_filename_returns_400(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/export",
            json={"content": {"name": "NoFilename"}},
        )
        assert resp.status_code == 400

    def test_missing_content_returns_400(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": "NoContent_test.json"},
        )
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, flask_server):
        resp = req.post(f"{flask_server}/api/export", data="not-json",
                        headers={"Content-Type": "text/plain"})
        assert resp.status_code == 400

    def test_path_traversal_is_sanitized(self, flask_server):
        """../evil.json must be sanitized so the file cannot escape the exports dir."""
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": "../evil.json", "content": {"exploit": True}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert ".." not in body["filename"], "Path traversal .. must be stripped from filename"
        assert "/" not in body["filename"], "Forward slash must be stripped from filename"

    def test_nested_path_traversal_is_sanitized(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/export",
            json={"filename": "../../etc/passwd", "content": {"exploit": True}},
        )
        assert resp.status_code == 200
        assert ".." not in resp.json()["filename"]


# ===========================================================================
# 13. API: GET /api/exports
# ===========================================================================

class TestAPIExports:

    def test_list_exports_returns_200(self, flask_server):
        assert req.get(f"{flask_server}/api/exports").status_code == 200

    def test_list_exports_success_true(self, flask_server):
        assert req.get(f"{flask_server}/api/exports").json()["success"] is True

    def test_list_exports_has_count_field(self, flask_server):
        assert "count" in req.get(f"{flask_server}/api/exports").json()

    def test_list_exports_has_exports_array(self, flask_server):
        assert isinstance(req.get(f"{flask_server}/api/exports").json()["exports"], list)

    def test_list_exports_count_matches_array_length(self, flask_server):
        body = req.get(f"{flask_server}/api/exports").json()
        assert body["count"] == len(body["exports"])

    def test_export_entry_has_required_fields(self, flask_server):
        # Ensure at least one export exists
        req.post(
            f"{flask_server}/api/export",
            json={"filename": "FieldCheck_Cleric_lvl6_fields.json", "content": {"x": 1}},
        )
        entries = req.get(f"{flask_server}/api/exports").json()["exports"]
        assert len(entries) > 0, "Should have at least one export after creating one"
        entry = entries[0]
        for field in ("filename", "size", "modified"):
            assert field in entry, f"Export entry missing field '{field}'"

    def test_export_entry_size_is_positive(self, flask_server):
        entries = req.get(f"{flask_server}/api/exports").json()["exports"]
        if entries:
            assert entries[0]["size"] > 0

    def test_export_entry_modified_is_iso_timestamp(self, flask_server):
        entries = req.get(f"{flask_server}/api/exports").json()["exports"]
        if entries:
            # ISO 8601 contains a 'T'
            assert "T" in entries[0]["modified"] or "-" in entries[0]["modified"]


# ===========================================================================
# 14. API: Console Log Endpoints
# ===========================================================================

class TestAPIConsoleLogs:

    def test_new_log_file_returns_200(self, flask_server):
        assert req.post(f"{flask_server}/api/console-log/new").status_code == 200

    def test_new_log_file_returns_success_true(self, flask_server):
        assert req.post(f"{flask_server}/api/console-log/new").json()["success"] is True

    def test_new_log_file_returns_filename(self, flask_server):
        body = req.post(f"{flask_server}/api/console-log/new").json()
        assert "filename" in body
        assert body["filename"].startswith("browser-console-")

    def test_new_log_file_returns_path(self, flask_server):
        body = req.post(f"{flask_server}/api/console-log/new").json()
        assert "path" in body

    def test_write_log_entry_returns_200(self, flask_server):
        req.post(f"{flask_server}/api/console-log/new")
        resp = req.post(
            f"{flask_server}/api/console-log",
            json={"entries": ["[2026-01-01T00:00:00Z] [LOG] Hello from test"]},
        )
        assert resp.status_code == 200

    def test_write_log_entry_returns_count(self, flask_server):
        req.post(f"{flask_server}/api/console-log/new")
        entries = [
            "[2026-01-01T00:00:00Z] [LOG] Entry A",
            "[2026-01-01T00:00:01Z] [WARN] Entry B",
        ]
        resp = req.post(f"{flask_server}/api/console-log", json={"entries": entries})
        assert resp.json()["count"] == 2

    def test_write_empty_entries_returns_200(self, flask_server):
        req.post(f"{flask_server}/api/console-log/new")
        resp = req.post(f"{flask_server}/api/console-log", json={"entries": []})
        assert resp.status_code == 200

    def test_write_log_missing_entries_key_returns_400(self, flask_server):
        resp = req.post(
            f"{flask_server}/api/console-log",
            json={"wrong_key": ["entry"]},
        )
        assert resp.status_code == 400

    def test_log_file_created_on_disk(self, flask_server):
        body = req.post(f"{flask_server}/api/console-log/new").json()
        fname = body.get("filename", "")
        repo = Path(__file__).parent.parent
        log_path = repo / "logs" / fname
        assert log_path.exists(), f"Log file '{fname}' was not created on disk"

    def test_log_entries_written_to_disk(self, flask_server):
        req.post(f"{flask_server}/api/console-log/new")
        message = "DISK_WRITE_VERIFICATION_UNIQUE_TOKEN"
        req.post(
            f"{flask_server}/api/console-log",
            json={"entries": [f"[2026-01-01T00:00:00Z] [LOG] {message}"]},
        )
        # Find the most recently modified console log
        repo = Path(__file__).parent.parent
        logs = sorted(
            (repo / "logs").glob("browser-console-*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        assert logs, "No console log files found"
        content = logs[0].read_text()
        assert message in content, "Written log entry not found in log file on disk"
