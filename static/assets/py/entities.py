"""Entity system - universal game object representation."""

from typing import Union



class Entity:
    """
    Base entity class - represents any displayable game object.
    Can be a spell, equipment, ability, resource, or custom entity.
    Provides unified interface for properties, serialization, and rendering.
    """
    def __init__(self, name: str, entity_type: str = "", description: str = ""):
        self.name = name
        self.entity_type = entity_type  # "spell", "equipment", "ability", "resource", etc.
        self.description = description
        self.properties = {}  # Dynamic properties - stores any key-value pairs
    
    def add_property(self, key: str, value):
        """Add or update a dynamic property"""
        self.properties[key] = value
        return self
    
    def get_property(self, key: str, default=None):
        """Get a property with optional default value"""
        return self.properties.get(key, default)
    
    def has_property(self, key: str) -> bool:
        """Check if property exists"""
        return key in self.properties
    
    def remove_property(self, key: str):
        """Remove a property"""
        if key in self.properties:
            del self.properties[key]
        return self
    
    def get_all_properties(self) -> dict:
        """Get all dynamic properties"""
        return self.properties.copy()
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "properties": self.properties.copy()
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Entity':
        """Create Entity from dictionary"""
        if not isinstance(data, dict):
            return data
        
        entity = Entity(
            name=data.get("name", "Unknown"),
            entity_type=data.get("entity_type", ""),
            description=data.get("description", "")
        )
        
        # Restore properties
        for key, value in data.get("properties", {}).items():
            entity.add_property(key, value)
        
        return entity
    
    def __repr__(self) -> str:
        return f"Entity(name='{self.name}', type='{self.entity_type}', props={len(self.properties)})"


class Spell(Entity):
    """
    Spell entity - represents a D&D 5e spell with all its properties.
    Inherits from Entity for unified property handling and serialization.
    """
    def __init__(self, name: str, level: int = 0, school: str = "", 
                 casting_time: str = "", duration: str = "", ritual: bool = False,
                 concentration: bool = False, components: str = "", 
                 slug: str = "", classes: list = None, source: str = "", **kwargs):
        super().__init__(name, entity_type="spell", **kwargs)
        self.level = level
        self.school = school
        self.casting_time = casting_time
        self.duration = duration
        self.ritual = ritual
        self.concentration = concentration
        self.components = components
        self.slug = slug
        self.classes = classes or []
        self.source = source
    
    def to_dict(self) -> dict:
        """Convert spell to dictionary"""
        d = super().to_dict()
        d.update({
            "level": self.level,
            "school": self.school,
            "casting_time": self.casting_time,
            "duration": self.duration,
            "ritual": self.ritual,
            "concentration": self.concentration,
            "components": self.components,
            "slug": self.slug,
            "classes": self.classes,
            "source": self.source,
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Spell':
        """Create Spell from dictionary"""
        if not isinstance(data, dict):
            return data
        
        spell = Spell(
            name=data.get("name", "Unknown"),
            level=data.get("level", 0),
            school=data.get("school", ""),
            casting_time=data.get("casting_time", ""),
            duration=data.get("duration", ""),
            ritual=data.get("ritual", False),
            concentration=data.get("concentration", False),
            components=data.get("components", ""),
            slug=data.get("slug", ""),
            classes=data.get("classes", []),
            source=data.get("source", ""),
            description=data.get("description", "")
        )
        
        # Restore dynamic properties
        for key, value in data.get("properties", {}).items():
            spell.add_property(key, value)
        
        return spell
    
    def __repr__(self) -> str:
        level_label = f"L{self.level}" if self.level > 0 else "Cantrip"
        return f"Spell(name='{self.name}', {level_label}, school='{self.school}')"


class Ability(Entity):
    """
    Ability entity - represents class features, feats, or special abilities.
    """
    def __init__(self, name: str, ability_type: str = "feature", level_gained: int = 1, **kwargs):
        super().__init__(name, entity_type="ability", **kwargs)
        self.ability_type = ability_type  # "feature", "feat", "trait", etc.
        self.level_gained = level_gained
    
    def to_dict(self) -> dict:
        """Convert ability to dictionary"""
        d = super().to_dict()
        d.update({
            "ability_type": self.ability_type,
            "level_gained": self.level_gained,
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Ability':
        """Create Ability from dictionary"""
        if not isinstance(data, dict):
            return data
        
        ability = Ability(
            name=data.get("name", "Unknown"),
            ability_type=data.get("ability_type", "feature"),
            level_gained=data.get("level_gained", 1),
            description=data.get("description", "")
        )
        
        for key, value in data.get("properties", {}).items():
            ability.add_property(key, value)
        
        return ability
    
    def __repr__(self) -> str:
        return f"Ability(name='{self.name}', type='{self.ability_type}', L{self.level_gained})"


class Resource(Entity):
    """
    Resource entity - represents trackable resources like Ki, Rage, Channel Divinity uses.
    Supports current/max value tracking and use/restore operations.
    """
    def __init__(self, name: str, max_value: int = 0, current_value: int = None, **kwargs):
        super().__init__(name, entity_type="resource", **kwargs)
        self.max_value = max_value
        self.current_value = current_value if current_value is not None else max_value
    
    def use(self, amount: int = 1) -> int:
        """
        Use resource by specified amount.
        Returns actual amount used (capped at current value).
        """
        actual_used = min(amount, self.current_value)
        self.current_value = max(0, self.current_value - amount)
        return actual_used
    
    def restore(self, amount: int = None) -> int:
        """
        Restore resource.
        If amount is None, restores to full.
        Returns amount restored.
        """
        if amount is None:
            restored = self.max_value - self.current_value
            self.current_value = self.max_value
        else:
            actual_restored = min(amount, self.max_value - self.current_value)
            self.current_value += actual_restored
            restored = actual_restored
        return restored
    
    def is_available(self, amount: int = 1) -> bool:
        """Check if enough resource is available"""
        return self.current_value >= amount
    
    def get_percent(self) -> int:
        """Get remaining resource as percentage"""
        if self.max_value == 0:
            return 0
        return int((self.current_value / self.max_value) * 100)
    
    def to_dict(self) -> dict:
        """Convert resource to dictionary"""
        d = super().to_dict()
        d.update({
            "max_value": self.max_value,
            "current_value": self.current_value,
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Resource':
        """Create Resource from dictionary"""
        if not isinstance(data, dict):
            return data
        
        resource = Resource(
            name=data.get("name", "Unknown"),
            max_value=data.get("max_value", 0),
            current_value=data.get("current_value"),
            description=data.get("description", "")
        )
        
        for key, value in data.get("properties", {}).items():
            resource.add_property(key, value)
        
        return resource
    
    def __repr__(self) -> str:
        return f"Resource(name='{self.name}', {self.current_value}/{self.max_value})"


class Equipment(Entity):
    """Equipment entity - base class for all equipment items"""
    def __init__(self, name: str, cost: str = "", weight: str = "", source: str = "", **kwargs):
        super().__init__(name, entity_type="equipment", **kwargs)
        self.cost = cost
        self.weight = weight
        self.source = source
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        d = super().to_dict()
        d.update({
            "cost": self.cost,
            "weight": self.weight,
            "source": self.source
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Equipment':
        """Create Equipment object from dictionary"""
        if not isinstance(data, dict):
            return data  # Already an object or invalid
        
        name = data.get("name", "Unknown")
        
        # Detect type and create appropriate subclass
        if data.get("damage"):
            return Weapon.from_dict(data)
        elif data.get("armor_class") and "shield" not in name.lower():
            return Armor.from_dict(data)
        elif data.get("ac"):
            return Shield.from_dict(data)
        else:
            # Default Equipment
            return Equipment(
                name=name,
                cost=data.get("cost", ""),
                weight=data.get("weight", ""),
                source=data.get("source", ""),
                description=data.get("description", "")
            )


class Weapon(Equipment):
    """Weapon equipment with damage properties"""
    def __init__(self, name: str, damage: str = "", damage_type: str = "", 
                 range_text: str = "", properties: str = "", **kwargs):
        super().__init__(name, **kwargs)
        self.damage = damage
        self.damage_type = damage_type
        self.range = range_text
        self.properties = properties
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.damage:
            d["damage"] = self.damage
        if self.damage_type:
            d["damage_type"] = self.damage_type
        if self.range:
            d["range"] = self.range
        if self.properties:
            d["properties"] = self.properties
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Weapon':
        """Create Weapon from dictionary"""
        return Weapon(
            name=data.get("name", "Unknown"),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            source=data.get("source", ""),
            damage=data.get("damage", ""),
            damage_type=data.get("damage_type", ""),
            range_text=data.get("range", ""),
            properties=data.get("properties", ""),
            description=data.get("description", "")
        )


class Armor(Equipment):
    """Armor equipment with AC value"""
    def __init__(self, name: str, armor_class: Union[int, str] = "", **kwargs):
        super().__init__(name, **kwargs)
        self.armor_class = armor_class
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.armor_class:
            d["armor_class"] = self.armor_class
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Armor':
        """Create Armor from dictionary"""
        return Armor(
            name=data.get("name", "Unknown"),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            source=data.get("source", ""),
            armor_class=data.get("armor_class", ""),
            description=data.get("description", "")
        )


class Shield(Equipment):
    """Shield equipment with AC bonus"""
    def __init__(self, name: str, ac_bonus: str = "", **kwargs):
        super().__init__(name, **kwargs)
        self.ac_bonus = ac_bonus
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.ac_bonus:
            d["ac"] = self.ac_bonus
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Shield':
        """Create Shield from dictionary"""
        return Shield(
            name=data.get("name", "Unknown"),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            source=data.get("source", ""),
            ac_bonus=data.get("ac", ""),
            description=data.get("description", "")
        )

