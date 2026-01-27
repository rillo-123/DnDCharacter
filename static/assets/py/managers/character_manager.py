"""
Character Manager - Manages character stats and provides to dependent managers.

Architecture:
- CharacterManager: Wraps Character instance and manages synchronization
  - Initializes from character data
  - Syncs form inputs to character model
  - Provides stats dict to entity managers (weapons, armor)
  - Single source of truth for all character stats

This follows the same manager pattern as:
- WeaponsCollectionManager (weapons_manager.py)
- ArmorCollectionManager (armor_manager.py)

All managers depend on CHARACTER_MANAGER for character stats.
"""

from typing import Dict, Optional, Any

try:
    from character_models import Character
except ImportError:
    Character = None

try:
    from js import console
except ImportError:
    class _MockConsole:
        @staticmethod
        def log(msg):
            print(f"[CHARACTER_MANAGER] {msg}")
        
        @staticmethod
        def error(msg):
            print(f"[CHARACTER_MANAGER ERROR] {msg}")
    
    console = _MockConsole()


class CharacterManager:
    """Manages character stats and serves as single source of truth for all managers.
    
    Responsibilities:
    - Owns the Character instance
    - Synchronizes form inputs with character model
    - Provides stats to entity managers (weapons, armor)
    - Calculates proficiency bonus from level
    """
    
    def __init__(self, character_data: Optional[Dict[str, Any]] = None):
        """Initialize CharacterManager with character data.
        
        Args:
            character_data: Character dictionary or Character instance
        """
        if Character is None:
            console.error("Character class not available")
            self.character = None
            return
        
        if isinstance(character_data, Character):
            self.character = character_data
        else:
            self.character = Character(character_data)
        
        console.log(f"CharacterManager initialized: {self.character.display_name()}")
    
    # ===================================================================
    # Character sync from form
    # ===================================================================
    
    def sync_from_form(self, form_getters: Dict[str, callable]) -> None:
        """Synchronize character from form inputs.
        
        Args:
            form_getters: Dict mapping field names to getter functions
                Example: {
                    "name": lambda: document.getElementById('name').value,
                    "level": lambda: int(document.getElementById('level').value or 1),
                    ...
                }
        """
        if self.character is None:
            return
        
        try:
            # Update identity fields
            if "name" in form_getters:
                self.character.name = form_getters["name"]()
            if "class" in form_getters:
                self.character.class_text = form_getters["class"]()
            if "race" in form_getters:
                self.character.race = form_getters["race"]()
            if "background" in form_getters:
                self.character.background = form_getters["background"]()
            if "alignment" in form_getters:
                self.character.alignment = form_getters["alignment"]()
            if "player_name" in form_getters:
                self.character.player_name = form_getters["player_name"]()
            if "subclass" in form_getters:
                self.character.subclass = form_getters["subclass"]()
            
            # Update level (affects proficiency bonus)
            if "level" in form_getters:
                self.character.level = form_getters["level"]()
            
            # Update ability scores
            for ability in ["str", "dex", "con", "int", "wis", "cha"]:
                field_name = f"{ability}-score"
                if field_name in form_getters:
                    self.character.attributes[ability] = form_getters[field_name]()
            
            console.log("CharacterManager synced from form")
        except Exception as e:
            console.error(f"Error syncing from form: {e}")
    
    # ===================================================================
    # Stats for entity managers
    # ===================================================================
    
    def get_stats_dict(self) -> Dict[str, int]:
        """Get character stats for entity managers.
        
        Returns:
            Dict with keys: str, dex, proficiency
        """
        if self.character is None:
            return {"str": 10, "dex": 10, "proficiency": 2}
        
        return self.character.get_stats_dict()
    
    def get_ability_modifier(self, ability: str) -> int:
        """Get ability modifier for a specific ability.
        
        Args:
            ability: Ability key ('str', 'dex', 'con', 'int', 'wis', 'cha')
        
        Returns:
            Ability modifier
        """
        if self.character is None:
            return 0
        
        return self.character.get_ability_modifier(ability)
    
    # ===================================================================
    # Character properties (delegated)
    # ===================================================================
    
    @property
    def level(self) -> int:
        """Character level."""
        if self.character is None:
            return 1
        return self.character.level
    
    @property
    def proficiency_bonus(self) -> int:
        """Proficiency bonus based on level."""
        if self.character is None:
            return 2
        return self.character.proficiency_bonus
    
    @property
    def name(self) -> str:
        """Character name."""
        if self.character is None:
            return ""
        return self.character.display_name()
    
    @property
    def class_text(self) -> str:
        """Character class text."""
        if self.character is None:
            return ""
        return self.character.class_text
    
    @property
    def race(self) -> str:
        """Character race."""
        if self.character is None:
            return ""
        return self.character.race
    
    @property
    def attributes(self):
        """Character attributes accessor."""
        if self.character is None:
            return None
        return self.character.attributes
    
    def to_dict(self) -> Dict[str, Any]:
        """Export character to dictionary."""
        if self.character is None:
            return {}
        return self.character.to_dict()


# Global instance and initialization function
_CHARACTER_MANAGER: Optional[CharacterManager] = None


def initialize_character_manager(character_data: Optional[Dict[str, Any]] = None) -> CharacterManager:
    """Initialize the global character manager.
    
    Args:
        character_data: Character dictionary
    
    Returns:
        CharacterManager instance
    """
    global _CHARACTER_MANAGER
    _CHARACTER_MANAGER = CharacterManager(character_data)
    return _CHARACTER_MANAGER


def get_character_manager() -> Optional[CharacterManager]:
    """Get the global character manager instance."""
    return _CHARACTER_MANAGER
