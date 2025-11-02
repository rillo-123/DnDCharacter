// D&D 5e Spell Database
const SPELL_DATABASE = {
  // Cantrips (Level 0)
  "acid-splash": {
    name: "Acid Splash",
    level: 0,
    school: "Conjuration",
    castingTime: "1 action",
    range: "60 feet",
    components: "V, S",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "You hurl a bubble of acid. Choose one creature within range, or choose two creatures within range that are within 5 feet of each other. A target must succeed on a Dexterity saving throw or take 1d6 acid damage. This spell's damage increases by 1d6 when you reach 5th level (2d6), 11th level (3d6), and 17th level (4d6)."
  },
  "fire-bolt": {
    name: "Fire Bolt",
    level: 0,
    school: "Evocation",
    castingTime: "1 action",
    range: "120 feet",
    components: "V, S",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "You hurl a mote of fire at a creature or object within range. Make a ranged spell attack against the target. On a hit, the target takes 1d10 fire damage. A flammable object hit by this spell ignites if it isn't being worn or carried. This spell's damage increases by 1d10 when you reach 5th level (2d10), 11th level (3d10), and 17th level (4d10)."
  },
  "mage-hand": {
    name: "Mage Hand",
    level: 0,
    school: "Conjuration",
    castingTime: "1 action",
    range: "30 feet",
    components: "V, S",
    duration: "1 minute",
    classes: ["wizard", "sorcerer", "bard", "warlock"],
    description: "A spectral, floating hand appears at a point you choose within range. The hand lasts for the duration or until you dismiss it as an action. The hand vanishes if it is ever more than 30 feet away from you or if you cast this spell again. You can use your action to control the hand. You can use the hand to manipulate an object, open an unlocked door or container, stow or retrieve an item from an open container, or pour the contents out of a vial."
  },
  "light": {
    name: "Light",
    level: 0,
    school: "Evocation",
    castingTime: "1 action",
    range: "Touch",
    components: "V, M (a firefly or phosphorescent moss)",
    duration: "1 hour",
    classes: ["wizard", "sorcerer", "bard", "cleric"],
    description: "You touch one object that is no larger than 10 feet in any dimension. Until the spell ends, the object sheds bright light in a 20-foot radius and dim light for an additional 20 feet. The light can be colored as you like. Completely covering the object with something opaque blocks the light. The spell ends if you cast it again or dismiss it as an action."
  },
  "sacred-flame": {
    name: "Sacred Flame",
    level: 0,
    school: "Evocation",
    castingTime: "1 action",
    range: "60 feet",
    components: "V, S",
    duration: "Instantaneous",
    classes: ["cleric"],
    description: "Flame-like radiance descends on a creature that you can see within range. The target must succeed on a Dexterity saving throw or take 1d8 radiant damage. The target gains no benefit from cover for this saving throw. The spell's damage increases by 1d8 when you reach 5th level (2d8), 11th level (3d8), and 17th level (4d8)."
  },
  "eldritch-blast": {
    name: "Eldritch Blast",
    level: 0,
    school: "Evocation",
    castingTime: "1 action",
    range: "120 feet",
    components: "V, S",
    duration: "Instantaneous",
    classes: ["warlock"],
    description: "A beam of crackling energy streaks toward a creature within range. Make a ranged spell attack against the target. On a hit, the target takes 1d10 force damage. The spell creates more than one beam when you reach higher levels: two beams at 5th level, three beams at 11th level, and four beams at 17th level."
  },

  // 1st Level Spells
  "magic-missile": {
    name: "Magic Missile",
    level: 1,
    school: "Evocation",
    castingTime: "1 action",
    range: "120 feet",
    components: "V, S",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. A dart deals 1d4 + 1 force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several. At Higher Levels: When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st."
  },
  "shield": {
    name: "Shield",
    level: 1,
    school: "Abjuration",
    castingTime: "1 reaction",
    range: "Self",
    components: "V, S",
    duration: "1 round",
    classes: ["wizard", "sorcerer"],
    description: "An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile."
  },
  "cure-wounds": {
    name: "Cure Wounds",
    level: 1,
    school: "Evocation",
    castingTime: "1 action",
    range: "Touch",
    components: "V, S",
    duration: "Instantaneous",
    classes: ["cleric", "druid", "bard", "paladin", "ranger"],
    description: "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier. This spell has no effect on undead or constructs. At Higher Levels: When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st."
  },
  "healing-word": {
    name: "Healing Word",
    level: 1,
    school: "Evocation",
    castingTime: "1 bonus action",
    range: "60 feet",
    components: "V",
    duration: "Instantaneous",
    classes: ["cleric", "druid", "bard"],
    description: "A creature of your choice that you can see within range regains hit points equal to 1d4 + your spellcasting ability modifier. This spell has no effect on undead or constructs. At Higher Levels: When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d4 for each slot level above 1st."
  },

  // 2nd Level Spells
  "misty-step": {
    name: "Misty Step",
    level: 2,
    school: "Conjuration",
    castingTime: "1 bonus action",
    range: "Self",
    components: "V",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer", "warlock"],
    description: "Briefly surrounded by silvery mist, you teleport up to 30 feet to an unoccupied space that you can see."
  },
  "mirror-image": {
    name: "Mirror Image",
    level: 2,
    school: "Illusion",
    castingTime: "1 action",
    range: "Self",
    components: "V, S",
    duration: "1 minute",
    classes: ["wizard", "sorcerer", "warlock"],
    description: "Three illusory duplicates of yourself appear in your space. Until the spell ends, the duplicates move with you and mimic your actions, shifting position so it's impossible to track which image is real. You can use your action to dismiss the illusory duplicates. Each time a creature targets you with an attack during the spell's duration, roll a d20 to determine whether the attack instead targets one of your duplicates."
  },
  "spiritual-weapon": {
    name: "Spiritual Weapon",
    level: 2,
    school: "Evocation",
    castingTime: "1 bonus action",
    range: "60 feet",
    components: "V, S",
    duration: "1 minute",
    classes: ["cleric"],
    description: "You create a floating, spectral weapon within range that lasts for the duration or until you cast this spell again. When you cast the spell, you can make a melee spell attack against a creature within 5 feet of the weapon. On a hit, the target takes force damage equal to 1d8 + your spellcasting ability modifier."
  },

  // 3rd Level Spells
  "fireball": {
    name: "Fireball",
    level: 3,
    school: "Evocation",
    castingTime: "1 action",
    range: "150 feet",
    components: "V, S, M (a tiny ball of bat guano and sulfur)",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame. Each creature in a 20-foot-radius sphere centered on that point must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one. At Higher Levels: When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd."
  },
  "counterspell": {
    name: "Counterspell",
    level: 3,
    school: "Abjuration",
    castingTime: "1 reaction",
    range: "60 feet",
    components: "S",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer", "warlock"],
    description: "You attempt to interrupt a creature in the process of casting a spell. If the creature is casting a spell of 3rd level or lower, its spell fails and has no effect. If it is casting a spell of 4th level or higher, make an ability check using your spellcasting ability. The DC equals 10 + the spell's level. On a success, the creature's spell fails and has no effect."
  },
  "revivify": {
    name: "Revivify",
    level: 3,
    school: "Necromancy",
    castingTime: "1 action",
    range: "Touch",
    components: "V, S, M (diamonds worth 300 gp, which the spell consumes)",
    duration: "Instantaneous",
    classes: ["cleric", "paladin"],
    description: "You touch a creature that has died within the last minute. That creature returns to life with 1 hit point. This spell can't return to life a creature that has died of old age, nor can it restore any missing body parts."
  },

  // 4th Level Spells
  "dimension-door": {
    name: "Dimension Door",
    level: 4,
    school: "Conjuration",
    castingTime: "1 action",
    range: "500 feet",
    components: "V",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer", "warlock", "bard"],
    description: "You teleport yourself from your current location to any other spot within range. You arrive at exactly the spot desired. It can be a place you can see, one you can visualize, or one you can describe by stating distance and direction. You can bring along objects as long as their weight doesn't exceed what you can carry. You can also bring one willing creature of your size or smaller."
  },
  "polymorph": {
    name: "Polymorph",
    level: 4,
    school: "Transmutation",
    castingTime: "1 action",
    range: "60 feet",
    components: "V, S, M (a caterpillar cocoon)",
    duration: "Concentration, up to 1 hour",
    classes: ["wizard", "sorcerer", "druid", "bard"],
    description: "This spell transforms a creature that you can see within range into a new form. An unwilling creature must make a Wisdom saving throw to avoid the effect. The spell has no effect on a shapechanger or a creature with 0 hit points. The transformation lasts for the duration, or until the target drops to 0 hit points or dies."
  },

  // 5th Level Spells
  "wall-of-force": {
    name: "Wall of Force",
    level: 5,
    school: "Evocation",
    castingTime: "1 action",
    range: "120 feet",
    components: "V, S, M (a pinch of powder made by crushing a clear gemstone)",
    duration: "Concentration, up to 10 minutes",
    classes: ["wizard"],
    description: "An invisible wall of force springs into existence at a point you choose within range. The wall appears in any orientation you choose, as a horizontal or vertical barrier or at an angle. It can be free floating or resting on a solid surface. You can form it into a hemispherical dome or a sphere with a radius of up to 10 feet, or you can shape a flat surface made up of ten 10-foot-by-10-foot panels."
  },
  "cone-of-cold": {
    name: "Cone of Cold",
    level: 5,
    school: "Evocation",
    castingTime: "1 action",
    range: "Self (60-foot cone)",
    components: "V, S, M (a small crystal or glass cone)",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "A blast of cold air erupts from your hands. Each creature in a 60-foot cone must make a Constitution saving throw. A creature takes 8d8 cold damage on a failed save, or half as much damage on a successful one. A creature killed by this spell becomes a frozen statue until it thaws."
  },

  // 6th Level Spells
  "disintegrate": {
    name: "Disintegrate",
    level: 6,
    school: "Transmutation",
    castingTime: "1 action",
    range: "60 feet",
    components: "V, S, M (a lodestone and a pinch of dust)",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "A thin green ray springs from your pointing finger to a target that you can see within range. The target can be a creature, an object, or a creation of magical force. A creature targeted by this spell must make a Dexterity saving throw. On a failed save, the target takes 10d6 + 40 force damage. If this damage reduces the target to 0 hit points, it is disintegrated."
  },

  // 7th Level Spells
  "teleport": {
    name: "Teleport",
    level: 7,
    school: "Conjuration",
    castingTime: "1 action",
    range: "10 feet",
    components: "V",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer", "bard"],
    description: "This spell instantly transports you and up to eight willing creatures of your choice that you can see within range, or a single object that you can see within range, to a destination you select. If you target an object, it must be able to fit entirely inside a 10-foot cube, and it can't be held or carried by an unwilling creature."
  },

  // 8th Level Spells
  "mind-blank": {
    name: "Mind Blank",
    level: 8,
    school: "Abjuration",
    castingTime: "1 action",
    range: "Touch",
    components: "V, S",
    duration: "24 hours",
    classes: ["wizard", "bard"],
    description: "Until the spell ends, one willing creature you touch is immune to psychic damage, any effect that would sense its emotions or read its thoughts, divination spells, and the charmed condition. The spell even foils wish spells and spells or effects of similar power used to affect the target's mind or to gain information about the target."
  },

  // 9th Level Spells
  "wish": {
    name: "Wish",
    level: 9,
    school: "Conjuration",
    castingTime: "1 action",
    range: "Self",
    components: "V",
    duration: "Instantaneous",
    classes: ["wizard", "sorcerer"],
    description: "Wish is the mightiest spell a mortal creature can cast. By simply speaking aloud, you can alter the very foundations of reality in accord with your desires. The basic use of this spell is to duplicate any other spell of 8th level or lower. You don't need to meet any requirements in that spell, including costly components. The spell simply takes effect."
  }
};

// Spell slot maximums by character level
const SPELL_SLOTS_BY_LEVEL = {
  1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
  2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
  3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
  4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
  5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
  6: [4, 3, 3, 0, 0, 0, 0, 0, 0],
  7: [4, 3, 3, 1, 0, 0, 0, 0, 0],
  8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
  9: [4, 3, 3, 3, 1, 0, 0, 0, 0],
  10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
  11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
  12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
  13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
  14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
  15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
  16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
  17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
  18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
  19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
  20: [4, 3, 3, 3, 3, 2, 2, 1, 1]
};
