"""
Base EntityManager class for managing and displaying D&D entities.

Pattern:
- EntityManager manages an entity (dict with raw data)
- Has properties like final_display_value that return formatted strings
- Subclasses implement entity-specific logic
- GUI just reads the display properties - no formatting logic there

This makes it easy to manage any entity: Weapon, Armor, ProfBonus, etc.
"""

from typing import Optional, Dict, Any


class EntityManager:
    """Base class for managing D&D entities with display properties."""
    
    def __init__(self, entity: Optional[Dict[str, Any]] = None):
        """Initialize manager with an entity (dict of raw data).
        
        Args:
            entity: Raw entity data as dictionary, or None
        """
        self.entity = entity or {}
    
    def set_entity(self, entity: Dict[str, Any]):
        """Update the entity data."""
        self.entity = entity
    
    def get_entity(self) -> Dict[str, Any]:
        """Get the raw entity data."""
        return self.entity
    
    @property
    def final_display_value(self) -> str:
        """Return the final display value for this entity.
        
        Must be overridden by subclasses.
        This is THE value that should be displayed in the GUI.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement final_display_value")
    
    def is_valid(self) -> bool:
        """Check if the entity is valid for display.
        
        Override in subclasses with specific validation.
        """
        return bool(self.entity)
