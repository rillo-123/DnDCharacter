"""
Tooltip Value Entities - Reusable tooltip calculation and rendering.

Provides a unified interface for calculating and displaying tooltips across
different parts of the character sheet (ability scores, weapon attacks, etc.)
using inheritance and composition.
"""

from typing import List, Optional, Dict


class TooltipValue:
    """Base class for values that display tooltips with breakdown information."""
    
    def __init__(self, label: str = "", total: int = 0):
        """
        Initialize a tooltip value.
        
        Args:
            label: Display label for the value
            total: The calculated total value
        """
        self.label = label
        self.total = total
        self.components: List[tuple] = []  # List of (component_label, component_value) tuples
    
    def add_component(self, label: str, value: int) -> 'TooltipValue':
        """Add a component to the breakdown. Returns self for chaining."""
        self.components.append((label, value))
        return self
    
    def recalculate_total(self) -> int:
        """Recalculate total from components."""
        self.total = sum(value for _, value in self.components)
        return self.total
    
    def format_bonus(self, value: int) -> str:
        """Format a value as a bonus string (+3, -1, or —)."""
        if value == 0:
            return "—"
        elif value > 0:
            return f"+{value}"
        else:
            return str(value)
    
    def generate_tooltip_html(self) -> str:
        """Generate HTML tooltip with breakdown. Override in subclasses."""
        if not self.components:
            return ""
        
        rows = []
        for comp_label, comp_value in self.components:
            rows.append(
                f'<div class="tooltip-row">'
                f'<span class="tooltip-label">{comp_label}</span>'
                f'<span class="tooltip-value">{self.format_bonus(comp_value)}</span>'
                f'</div>'
            )
        
        return f'<div class="stat-tooltip multiline">{"".join(rows)}</div>'
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(label='{self.label}', total={self.total}, components={len(self.components)})"


class AbilityScoreValue(TooltipValue):
    """Tooltip value for ability scores (STR, DEX, etc.)."""
    
    def __init__(self, ability: str = "", base_score: int = 10, race_bonus: int = 0):
        """
        Initialize ability score tooltip.
        
        Args:
            ability: Ability name (str, dex, con, int, wis, cha)
            base_score: Base ability score
            race_bonus: Racial bonus to the score
        """
        self.ability = ability.upper()
        self.base_score = base_score
        self.race_bonus = race_bonus
        total = base_score + race_bonus
        
        super().__init__(label=self.ability, total=total)
        
        # Add components
        self.add_component(f"Base {self.ability}", base_score)
        if race_bonus:
            self.add_component(f"Race bonus", race_bonus)
    
    def generate_tooltip_html(self) -> str:
        """Generate HTML tooltip for ability score breakdown."""
        rows = []
        for comp_label, comp_value in self.components:
            rows.append(
                f'<div class="tooltip-row">'
                f'<span class="tooltip-label">{comp_label}</span>'
                f'<span class="tooltip-value">{comp_value}</span>'
                f'</div>'
            )
        
        return f'<div class="stat-tooltip multiline">{"".join(rows)}</div>'


class SaveValue(TooltipValue):
    """Tooltip value for saving throws (ability saves)."""
    
    def __init__(self, ability: str = "", ability_mod: int = 0, proficiency: int = 0, 
                 is_proficient: bool = False, item_modifiers: int = 0):
        """
        Initialize save tooltip.
        
        Args:
            ability: Ability name (str, dex, etc.)
            ability_mod: Ability modifier
            proficiency: Proficiency bonus
            is_proficient: Whether character is proficient in this save
            item_modifiers: Bonuses from magic items
        """
        self.ability = ability.upper()
        total = ability_mod + (proficiency if is_proficient else 0) + item_modifiers
        
        super().__init__(label=f"{self.ability} Save", total=total)
        
        self.add_component(f"Ability mod ({self.ability})", ability_mod)
        
        if is_proficient:
            self.add_component("Proficiency", proficiency)
        
        if item_modifiers:
            self.add_component("Item modifiers", item_modifiers)


class SkillValue(TooltipValue):
    """Tooltip value for skill checks."""
    
    def __init__(self, skill_name: str = "", ability: str = "", ability_mod: int = 0,
                 race_bonus: int = 0, proficiency: int = 0, is_proficient: bool = False,
                 is_expertise: bool = False):
        """
        Initialize skill tooltip.
        
        Args:
            skill_name: Skill name (Acrobatics, etc.)
            ability: Ability key (dex, str, etc.)
            ability_mod: Ability modifier
            race_bonus: Racial bonus
            proficiency: Proficiency bonus
            is_proficient: Whether proficient in skill
            is_expertise: Whether has expertise in skill
        """
        self.skill_name = skill_name
        self.ability = ability.upper()
        
        total = ability_mod
        if race_bonus:
            total += race_bonus
        if is_expertise:
            total += proficiency * 2
        elif is_proficient:
            total += proficiency
        
        super().__init__(label=skill_name, total=total)
        
        self.add_component(f"{self.ability} mod", ability_mod)
        
        if race_bonus:
            self.add_component("Race bonus", race_bonus)
        
        if is_expertise:
            self.add_component("Expertise", proficiency * 2)
        elif is_proficient:
            self.add_component("Proficiency", proficiency)


class WeaponToHitValue(TooltipValue):
    """Tooltip value for weapon attack rolls (to-hit)."""
    
    def __init__(self, weapon_name: str = "", ability: str = "", ability_mod: int = 0,
                 proficiency: int = 0, weapon_bonus: int = 0):
        """
        Initialize weapon to-hit tooltip.
        
        Args:
            weapon_name: Name of the weapon
            ability: Ability used (str or dex)
            ability_mod: Ability modifier
            proficiency: Proficiency bonus
            weapon_bonus: Magical bonus on the weapon (+1, +2, etc.)
        """
        self.weapon_name = weapon_name
        self.ability = ability.upper()
        
        total = ability_mod + proficiency + weapon_bonus
        
        super().__init__(label=weapon_name, total=total)
        
        self.add_component(f"{self.ability} mod", ability_mod)
        self.add_component("Proficiency", proficiency)
        
        if weapon_bonus:
            self.add_component("Weapon bonus", weapon_bonus)


class DamageValue(TooltipValue):
    """Tooltip value for weapon damage rolls."""
    
    def __init__(self, damage_dice: str = "", damage_type: str = "", ability_mod: int = 0,
                 weapon_bonus: int = 0):
        """
        Initialize damage tooltip.
        
        Args:
            damage_dice: Damage dice formula (1d8, 2d6, etc.)
            damage_type: Type of damage (slashing, piercing, etc.)
            ability_mod: Ability modifier added to damage
            weapon_bonus: Magical bonus on the weapon
        """
        self.damage_dice = damage_dice
        self.damage_type = damage_type
        
        super().__init__(label=f"{damage_dice} {damage_type}".strip(), total=0)
        
        if ability_mod or weapon_bonus:
            total = ability_mod + weapon_bonus
            self.add_component("Ability mod", ability_mod)
            if weapon_bonus:
                self.add_component("Weapon bonus", weapon_bonus)
            self.total = total


# Utility function for formatting tooltips
def format_tooltip_html(title: str, rows: List[tuple]) -> str:
    """
    Format a multi-line tooltip with title and rows.
    
    Args:
        title: Tooltip title (optional)
        rows: List of (label, value) tuples
    
    Returns:
        HTML string for tooltip
    """
    html_rows = []
    
    if title:
        html_rows.append(
            f'<div class="tooltip-row">'
            f'<span class="tooltip-label" style="font-weight: 600;">{title}</span>'
            f'</div>'
        )
    
    for label, value in rows:
        # Format value if it's a number
        if isinstance(value, int):
            formatted_value = f"+{value}" if value > 0 else str(value)
        else:
            formatted_value = str(value)
        
        html_rows.append(
            f'<div class="tooltip-row">'
            f'<span class="tooltip-label">{label}</span>'
            f'<span class="tooltip-value">{formatted_value}</span>'
            f'</div>'
        )
    
    return f'<div class="stat-tooltip multiline">{"".join(html_rows)}</div>'
