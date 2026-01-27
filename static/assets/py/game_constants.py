"""D&D 5e Game Constants and Rules Data.

This module contains all hardcoded D&D 5e game rules data including armor classifications,
armor AC values, and other constants that should not be mixed with business logic.
"""

# =============================================================================
# Armor Classifications (by weight category)
# =============================================================================

ARMOR_TYPES = {
    "light": ["leather", "studded leather", "studded"],
    "medium": ["hide", "chain shirt", "scale mail", "breastplate", "half plate"],
    "heavy": ["plate", "chain mail", "splint", "splint armor"],
}

# =============================================================================
# Armor AC Values (from PHB)
# =============================================================================

# D&D 5e standard armor AC values (Player's Handbook, Chapter 5: Equipment)
ARMOR_AC_VALUES = {
    "leather": 11,
    "studded leather": 12,
    "studded": 12,
    "hide": 12,
    "chain shirt": 13,
    "scale mail": 14,
    "breastplate": 14,
    "half plate": 15,
    "plate": 18,
    "chain mail": 16,
    "splint": 17,
    "splint armor": 17,
    "shield": 2,  # Base shield AC bonus (actual total = base 2 + magic bonus)
}

# =============================================================================
# Utility Functions
# =============================================================================

def get_armor_type(armor_name: str) -> str:
    """Determine armor type (light, medium, heavy) from armor name.
    
    Args:
        armor_name: Name of the armor item (e.g., "Breastplate +1")
    
    Returns:
        String: "light", "medium", "heavy", or "unknown"
    """
    name_lower = armor_name.lower()
    for armor_type, names in ARMOR_TYPES.items():
        for name_pattern in names:
            if name_pattern in name_lower:
                return armor_type
    return "unknown"


def get_armor_ac(armor_name: str) -> int:
    """Get standard D&D 5e AC value for armor by name.
    
    Args:
        armor_name: Name of the armor item (e.g., "breastplate", "plate")
    
    Returns:
        Integer AC value, or None if not standard armor
    """
    name_lower = armor_name.lower()
    for armor_pattern, ac_value in ARMOR_AC_VALUES.items():
        if armor_pattern in name_lower:
            return ac_value
    return None
