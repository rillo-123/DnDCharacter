const LOCAL_STORAGE_KEY = "pysheet.character.v1";
const SPELL_CACHE_KEY = "pysheet.spells.v1";
const EQUIPMENT_CACHE_KEY = "dnd_equipment_cache_v10";

const ABILITIES = ["str", "dex", "con", "int", "wis", "cha"];
const CURRENCY = ["pp", "gp", "ep", "sp", "cp"];
const SKILL_ABILITIES = {
  acrobatics: "dex",
  animal_handling: "wis",
  arcana: "int",
  athletics: "str",
  deception: "cha",
  history: "int",
  insight: "wis",
  intimidation: "cha",
  investigation: "int",
  medicine: "wis",
  nature: "int",
  perception: "wis",
  performance: "cha",
  persuasion: "cha",
  religion: "int",
  sleight_of_hand: "dex",
  stealth: "dex",
  survival: "wis",
};

const CLASS_INFO = {
  barbarian: { hitDie: "d12", spellAbility: "str", armor: ["Light", "Medium", "Shield"], weapons: ["Simple", "Martial"] },
  bard: { hitDie: "d8", spellAbility: "cha", armor: ["Light"], weapons: ["Simple", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"] },
  cleric: { hitDie: "d8", spellAbility: "wis", armor: ["Light", "Medium", "Shield"], weapons: ["Simple"] },
  druid: { hitDie: "d8", spellAbility: "wis", armor: ["Light", "Medium", "Shield"], weapons: ["Club", "Dagger", "Dart", "Javelin", "Mace", "Quarterstaff", "Scimitar", "Sickle", "Sling", "Spear"] },
  fighter: { hitDie: "d10", spellAbility: "str", armor: ["Light", "Medium", "Heavy", "Shield"], weapons: ["Simple", "Martial"] },
  monk: { hitDie: "d8", spellAbility: "wis", armor: [], weapons: ["Simple", "Shortsword"] },
  paladin: { hitDie: "d10", spellAbility: "cha", armor: ["Light", "Medium", "Heavy", "Shield"], weapons: ["Simple", "Martial"] },
  ranger: { hitDie: "d10", spellAbility: "wis", armor: ["Light", "Medium", "Shield"], weapons: ["Simple", "Martial"] },
  rogue: { hitDie: "d8", spellAbility: "dex", armor: ["Light"], weapons: ["Simple", "Hand Crossbow", "Longsword", "Rapier", "Shortsword"] },
  sorcerer: { hitDie: "d6", spellAbility: "cha", armor: [], weapons: ["Dagger", "Dart", "Sling", "Quarterstaff", "Light Crossbow"] },
  warlock: { hitDie: "d8", spellAbility: "cha", armor: ["Light"], weapons: ["Simple"] },
  wizard: { hitDie: "d6", spellAbility: "int", armor: [], weapons: ["Dagger", "Dart", "Sling", "Quarterstaff", "Light Crossbow"] },
};

const RACE_BONUSES = {
  human: { str: 1, dex: 1, con: 1, int: 1, wis: 1, cha: 1 },
  elf: { dex: 2 },
  "high elf": { dex: 2, int: 1 },
  "wood elf": { dex: 2, wis: 1 },
  "dark elf": { dex: 2, cha: 1 },
  dwarf: { con: 2 },
  "mountain dwarf": { str: 2, con: 2 },
  "hill dwarf": { con: 2, wis: 1 },
  halfling: { dex: 2 },
  "lightfoot halfling": { dex: 2, cha: 1 },
  "stout halfling": { dex: 2, con: 1 },
  dragonborn: { str: 2, cha: 1 },
  gnome: { int: 2 },
  "half-elf": { cha: 2 },
  "half-orc": { str: 2, con: 1 },
  tiefling: { int: 1, cha: 2 },
};

const STANDARD_SLOT_TABLE = {
  1: { 1: 2 },
  2: { 1: 3 },
  3: { 1: 4, 2: 2 },
  4: { 1: 4, 2: 3 },
  5: { 1: 4, 2: 3, 3: 2 },
  6: { 1: 4, 2: 3, 3: 3 },
  7: { 1: 4, 2: 3, 3: 3, 4: 1 },
  8: { 1: 4, 2: 3, 3: 3, 4: 2 },
  9: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 1 },
  10: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2 },
  11: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1 },
  12: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1 },
  13: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1 },
  14: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1 },
  15: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1 },
  16: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1 },
  17: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1 },
  18: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1 },
  19: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1 },
  20: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1 },
};

const CASTER_CLASSES = new Set(["bard", "cleric", "druid", "sorcerer", "wizard"]);
const HALF_CASTER_CLASSES = new Set(["paladin", "ranger"]);
const PACT_CLASSES = new Set(["warlock"]);

const CLASS_FEATURES = {
  cleric: {
    1: [
      ["Spellcasting", "You can prepare cleric spells and cast them using Wisdom."],
      ["Divine Domain", "Choose a cleric domain. Domain spells are always prepared."],
    ],
    2: [["Channel Divinity", "You can channel divine energy to fuel magical effects such as Turn Undead."]],
    5: [["Destroy Undead", "When an undead fails its save against Turn Undead, it may be destroyed based on CR."]],
    10: [["Divine Intervention", "You can call on your deity for aid."]],
  },
  bard: {
    1: [["Bardic Inspiration", "Use a bonus action to inspire another creature within 60 feet."]],
    2: [["Jack of All Trades", "Add half your proficiency bonus to ability checks that do not already include proficiency."]],
    3: [["Bard College", "Choose a bard college and gain its features."]],
  },
  fighter: {
    1: [["Fighting Style", "Adopt a particular style of fighting."], ["Second Wind", "Regain hit points as a bonus action once per rest."]],
    2: [["Action Surge", "Take one additional action on your turn once per rest."]],
  },
};

const DOMAIN_FEATURES = {
  life: {
    1: [
      ["Bonus Proficiency", "You gain proficiency with heavy armor."],
      ["Disciple of Life", "Healing spells restore additional hit points equal to 2 + the spell level."],
    ],
    2: [["Channel Divinity: Preserve Life", "Restore hit points equal to five times your cleric level, divided among creatures you can see."]],
    6: [["Blessed Healer", "Healing others with a spell also heals you."]],
    8: [["Divine Strike", "Weapon attacks can deal extra radiant damage once per turn."]],
    17: [["Supreme Healing", "Use the highest result possible for healing dice."]],
  },
};

const DOMAIN_SPELLS = {
  life: {
    1: ["bless", "cure-wounds"],
    3: ["lesser-restoration", "spiritual-weapon"],
    5: ["beacon-of-hope", "revivify"],
    7: ["death-ward", "guardian-of-faith"],
    9: ["mass-cure-wounds", "raise-dead"],
  },
  knowledge: { 1: ["detect-magic", "bless"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  tempest: { 1: ["faerie-fire", "shatter"], 3: ["hold-person", "confusion"], 5: ["insect-plague", "mass-cure-wounds"] },
  trickery: { 1: ["faerie-fire", "vicious-mockery"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  war: { 1: ["bless", "guiding-bolt"], 3: ["hold-person", "shatter"], 5: ["insect-plague", "raise-dead"] },
  light: { 1: ["guiding-bolt", "sacred-flame"], 3: ["shatter", "hold-person"], 5: ["insect-plague", "mass-cure-wounds"] },
  nature: { 1: ["faerie-fire", "detect-magic"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  forge: { 1: ["detect-magic", "bless"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  grave: { 1: ["bless", "detect-magic"], 3: ["hold-person", "shatter"], 5: ["confusion", "raise-dead"] },
  death: { 1: ["bless", "detect-magic"], 3: ["hold-person", "shatter"], 5: ["confusion", "raise-dead"] },
  arcana: { 1: ["detect-magic", "bless"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  city: { 1: ["detect-magic", "faerie-fire"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  order: { 1: ["bless", "guiding-bolt"], 3: ["hold-person", "shatter"], 5: ["confusion", "insect-plague"] },
  peace: { 1: ["bless", "detect-magic"], 3: ["healing-word", "prayer-of-healing"], 5: ["mass-cure-wounds", "raise-dead"] },
};

let inventoryItems = [];
let equipmentLibrary = [];
let spellLibrary = [];
let spellMap = new Map();
let spellSlotsUsed = {};
let preparedSpells = [];
let feats = [];
let suppressAutosave = false;
let saveTimer = null;

const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
const key = (value) => String(value || "").trim().toLowerCase();
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const uid = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

function numberValue(id, fallback = 0) {
  const element = $(id);
  if (!element) return fallback;
  const parsed = Number.parseInt(element.value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function textValue(id) {
  const element = $(id);
  return element ? String(element.value || "") : "";
}

function checked(id) {
  const element = $(id);
  return Boolean(element && element.checked);
}

function setValue(id, value) {
  const element = $(id);
  if (!element) return;
  if (element.type === "checkbox") {
    element.checked = Boolean(value);
  } else {
    element.value = value ?? "";
  }
}

function setText(id, value) {
  const element = $(id);
  if (element) element.textContent = String(value ?? "");
}

function setHtml(id, value) {
  const element = $(id);
  if (element) element.innerHTML = value ?? "";
}

function classKey() {
  return key(textValue("class").split(/\s+/)[0]);
}

function level() {
  return clamp(numberValue("level", 1), 1, 20);
}

function proficiencyBonus(lvl = level()) {
  return 2 + Math.floor((lvl - 1) / 4);
}

function mod(score) {
  return Math.floor((score - 10) / 2);
}

function fmtBonus(value) {
  return value >= 0 ? `+${value}` : String(value);
}

function raceBonus(ability) {
  const bonuses = RACE_BONUSES[key(textValue("race"))] || {};
  return Number(bonuses[ability] || 0);
}

function abilityScore(ability) {
  return numberValue(`${ability}-score`, 10) + raceBonus(ability);
}

function abilityMod(ability) {
  return mod(abilityScore(ability));
}

function spellAbility() {
  const explicit = textValue("spell_ability");
  if (explicit) return explicit;
  return CLASS_INFO[classKey()]?.spellAbility || "int";
}

function parseNumber(value, fallback = 0) {
  const match = String(value ?? "").match(/-?\d+(\.\d+)?/);
  return match ? Number.parseFloat(match[0]) : fallback;
}

function parseCostGp(value) {
  const text = String(value ?? "").toLowerCase();
  const amount = parseNumber(text, 0);
  if (text.includes("pp")) return amount * 10;
  if (text.includes("ep")) return amount * 0.5;
  if (text.includes("sp")) return amount * 0.1;
  if (text.includes("cp")) return amount * 0.01;
  return amount;
}

function itemQuantity(item) {
  return Math.max(1, Number.parseInt(item.quantity ?? item.qty ?? 1, 10) || 1);
}

function itemProperties(item) {
  if (Array.isArray(item.properties)) return item.properties.map(String);
  return String(item.properties || "")
    .split(/[,;]+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function itemCategory(item) {
  const explicit = item.category || item.type || item.equipment_category || "";
  if (explicit) return String(explicit);
  if (isWeapon(item)) return "Weapons";
  if (isArmor(item)) return "Armor";
  if (isShield(item)) return "Shields";
  return "Adventuring Gear";
}

function isWeapon(item) {
  return Boolean(item.damage || item.damage_dice || /weapon/i.test(itemCategoryRaw(item)));
}

function itemCategoryRaw(item) {
  return String(item.category || item.type || item.equipment_category || "");
}

function isShield(item) {
  return /shield/i.test(item.name || "") || /shield/i.test(itemCategoryRaw(item));
}

function isArmor(item) {
  if (isShield(item)) return false;
  return Boolean(item.armor_class || item.ac || /armor/i.test(itemCategoryRaw(item)) || /mail|plate|leather|hide|breastplate|splint/i.test(item.name || ""));
}

function armorBase(item) {
  if (isShield(item)) return 0;
  const raw = item.armor_class ?? item.ac ?? "";
  if (typeof raw === "object" && raw !== null) return Number(raw.base ?? raw.value ?? 0) || 0;
  return parseNumber(raw, 0);
}

function armorType(item) {
  const text = `${item.armor_category || item.category || item.type || ""} ${item.name || ""}`.toLowerCase();
  if (/heavy|ring mail|chain mail|splint|plate/.test(text)) return "Heavy";
  if (/medium|hide|chain shirt|scale mail|breastplate|half plate/.test(text)) return "Medium";
  if (/light|padded|leather|studded/.test(text)) return "Light";
  return isArmor(item) ? "Armor" : "";
}

function magicBonus(item) {
  const text = `${item.name || ""} ${item.bonus || ""} ${item.ac || ""}`;
  const match = text.match(/\+(\d+)/);
  return match ? Number.parseInt(match[1], 10) : 0;
}

function computeArmorClass() {
  const dex = abilityMod("dex");
  let ac = 10 + dex;
  let equippedArmor = inventoryItems.filter((item) => item.equipped && isArmor(item)).sort((a, b) => armorBase(b) - armorBase(a))[0];
  if (equippedArmor) {
    const base = armorBase(equippedArmor);
    const type = armorType(equippedArmor);
    let dexBonus = dex;
    if (type === "Medium") dexBonus = Math.min(2, dex);
    if (type === "Heavy") dexBonus = 0;
    ac = base + dexBonus + magicBonus(equippedArmor);
  }
  for (const shield of inventoryItems.filter((item) => item.equipped && isShield(item))) {
    ac += 2 + magicBonus(shield);
  }
  for (const item of inventoryItems.filter((item) => item.equipped && !isArmor(item) && !isShield(item))) {
    if (/protection/i.test(item.name || "")) ac += magicBonus(item);
  }
  return ac;
}

function defaultState() {
  return {
    identity: {
      name: "",
      class: "Wizard",
      race: "Human",
      background: "Sage",
      alignment: "Neutral Good",
      player_name: "",
      domain: "",
      subclass: "",
    },
    level: 1,
    abilities: Object.fromEntries(ABILITIES.map((ability) => [ability, { score: 10, save_proficient: false }])),
    skills: Object.fromEntries(Object.keys(SKILL_ABILITIES).map((skill) => [skill, { proficient: false, expertise: false }])),
    combat: {
      speed: 30,
      max_hp: 8,
      current_hp: 8,
      temp_hp: 0,
      hit_dice_available: 0,
      channel_divinity_available: 0,
      death_saves_success: 0,
      death_saves_failure: 0,
    },
    inventory: { items: [], currency: Object.fromEntries(CURRENCY.map((coin) => [coin, 0])) },
    spellcasting: { prepared: [], slots_used: {}, pact_used: 0 },
    feats: [],
  };
}

function collectCharacterData() {
  const abilityData = {};
  for (const ability of ABILITIES) {
    abilityData[ability] = {
      score: numberValue(`${ability}-score`, 10),
      save_proficient: checked(`${ability}-save-prof`),
    };
  }

  const skillData = {};
  for (const skill of Object.keys(SKILL_ABILITIES)) {
    skillData[skill] = {
      proficient: checked(`${skill}-prof`),
      expertise: checked(`${skill}-exp`),
      bonus: computeSkillTotal(skill),
    };
  }

  const data = {
    identity: {
      name: textValue("name"),
      class: textValue("class"),
      race: textValue("race"),
      background: textValue("background"),
      alignment: textValue("alignment"),
      player_name: textValue("player_name"),
      domain: textValue("domain"),
      subclass: textValue("domain"),
    },
    level: level(),
    spell_ability: spellAbility(),
    abilities: abilityData,
    skills: skillData,
    combat: {
      total_armor_class: computeArmorClass(),
      speed: numberValue("speed", 30),
      max_hp: numberValue("max_hp", 8),
      current_hp: numberValue("current_hp", 8),
      temp_hp: numberValue("temp_hp", 0),
      hit_dice: `${level()}${CLASS_INFO[classKey()]?.hitDie || "d8"}`,
      hit_dice_available: numberValue("hit_dice_available", 0),
      channel_divinity_available: numberValue("channel_divinity_available", 0),
      death_saves_success: [1, 2, 3].filter((i) => checked(`death_saves_success_${i}`)).length,
      death_saves_failure: [1, 2, 3].filter((i) => checked(`death_saves_failure_${i}`)).length,
    },
    inventory: {
      items: inventoryItems,
      currency: Object.fromEntries(CURRENCY.map((coin) => [coin, numberValue(`currency-${coin}`, 0)])),
    },
    spellcasting: {
      prepared: preparedSpells,
      slots_used: spellSlotsUsed,
      pact_used: 0,
    },
    feats,
    migration: {
      runtime: "javascript",
    },
  };
  return data;
}

function populateForm(data) {
  const state = { ...defaultState(), ...(data || {}) };
  const identity = state.identity || {};
  suppressAutosave = true;
  setValue("name", identity.name || "");
  setValue("class", normalizeClassName(identity.class || "Wizard"));
  setValue("race", identity.race || "Human");
  setValue("background", identity.background || "Sage");
  setValue("alignment", identity.alignment || "Neutral Good");
  setValue("player_name", identity.player_name || "");
  setValue("domain", identity.domain || identity.subclass || "");
  setValue("level", state.level || 1);

  for (const ability of ABILITIES) {
    const entry = state.abilities?.[ability] || {};
    setValue(`${ability}-score`, entry.score ?? 10);
    setValue(`${ability}-save-prof`, entry.save_proficient ?? entry.proficient ?? false);
  }
  for (const skill of Object.keys(SKILL_ABILITIES)) {
    const entry = state.skills?.[skill] || {};
    setValue(`${skill}-prof`, entry.proficient ?? false);
    setValue(`${skill}-exp`, entry.expertise ?? false);
  }

  const combat = state.combat || {};
  setValue("speed", combat.speed ?? 30);
  setValue("max_hp", combat.max_hp ?? 8);
  setValue("current_hp", combat.current_hp ?? combat.max_hp ?? 8);
  setValue("temp_hp", combat.temp_hp ?? 0);
  setValue("hit_dice_available", combat.hit_dice_available ?? 0);
  setValue("channel_divinity_available", combat.channel_divinity_available ?? 0);
  for (const i of [1, 2, 3]) {
    setValue(`death_saves_success_${i}`, i <= (combat.death_saves_success || 0));
    setValue(`death_saves_failure_${i}`, i <= (combat.death_saves_failure || 0));
  }

  inventoryItems = Array.isArray(state.inventory?.items) ? state.inventory.items.map(normalizeItem) : [];
  for (const coin of CURRENCY) setValue(`currency-${coin}`, state.inventory?.currency?.[coin] ?? 0);
  spellSlotsUsed = { ...(state.spellcasting?.slots_used || {}) };
  preparedSpells = Array.isArray(state.spellcasting?.prepared) ? state.spellcasting.prepared.map(normalizePrepared) : [];
  feats = Array.isArray(state.feats) ? state.feats : [];

  suppressAutosave = false;
  renderAll();
}

function normalizeClassName(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const first = text.split(/\s+/)[0].toLowerCase();
  return first.charAt(0).toUpperCase() + first.slice(1);
}

function normalizeItem(item) {
  const copy = { ...item };
  copy.id = copy.id || uid();
  copy.name = copy.name || "Unnamed Item";
  copy.category = itemCategory(copy);
  copy.quantity = itemQuantity(copy);
  copy.equipped = Boolean(copy.equipped);
  return copy;
}

function normalizePrepared(entry) {
  if (typeof entry === "string") return { slug: entry, is_domain_bonus: false };
  return { slug: entry.slug, is_domain_bonus: Boolean(entry.is_domain_bonus) };
}

function saveCharacter({ quiet = false } = {}) {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(collectCharacterData()));
  if (!quiet) setSavingMessage("Saved", "saving");
}

function scheduleSave() {
  if (suppressAutosave) return;
  setSavingMessage("Saving", "recording");
  window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    saveCharacter({ quiet: true });
    setSavingMessage("Saved", "saving");
  }, 250);
}

function setSavingMessage(message, stateClass = "") {
  const indicator = $("saving-indicator");
  if (!indicator) return;
  indicator.classList.remove("recording", "saving", "fading");
  if (stateClass) indicator.classList.add(stateClass);
  const text = indicator.querySelector(".saving-text");
  if (text) text.textContent = message;
}

function loadInitialState() {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (raw) {
      populateForm(JSON.parse(raw));
      return;
    }
  } catch (error) {
    console.warn("Unable to load saved character", error);
  }
  populateForm(defaultState());
}

function updateCalculations() {
  const prof = proficiencyBonus();
  setText("proficiency-bonus", fmtBonus(prof));
  for (const ability of ABILITIES) {
    const bonus = raceBonus(ability);
    const total = abilityScore(ability);
    const abilityModifier = mod(total);
    setText(`${ability}-race`, bonus ? fmtBonus(bonus) : "-");
    setText(`${ability}-total`, total);
    setText(`${ability}-mod`, fmtBonus(abilityModifier));
    setText(`${ability}-save`, fmtBonus(abilityModifier + (checked(`${ability}-save-prof`) ? prof : 0)));
  }
  for (const skill of Object.keys(SKILL_ABILITIES)) {
    setText(`${skill}-total`, fmtBonus(computeSkillTotal(skill)));
  }
  setText("passive-perception", 10 + computeSkillTotal("perception"));
  setText("passive-insight", 10 + computeSkillTotal("insight"));
  setText("passive-investigation", 10 + computeSkillTotal("investigation"));
  setText("initiative", fmtBonus(abilityMod("dex")));
  setText("total_armor_class", computeArmorClass());
  const info = CLASS_INFO[classKey()] || CLASS_INFO.wizard;
  setText("hit_dice", `${level()}${info.hitDie}`);
  const spellMod = abilityMod(spellAbility());
  setText("spell-save-dc", 8 + prof + spellMod);
  setText("spell-attack", fmtBonus(prof + spellMod));
  setText("concentration-save", `1d20 ${fmtBonus(abilityMod("con") + (checked("con-save-prof") ? prof : 0))} vs DC 10`);
  renderHealth();
  renderProficiencies();
}

function computeSkillTotal(skill) {
  const prof = proficiencyBonus();
  const base = abilityMod(SKILL_ABILITIES[skill] || "int");
  if (checked(`${skill}-exp`)) return base + prof * 2;
  if (checked(`${skill}-prof`)) return base + prof;
  return base;
}

function renderHealth() {
  const maxHp = Math.max(1, numberValue("max_hp", 1));
  const current = clamp(numberValue("current_hp", maxHp), 0, maxHp);
  const temp = Math.max(0, numberValue("temp_hp", 0));
  setValue("current_hp", current);
  const hpPercent = clamp((current / maxHp) * 100, 0, 100);
  const tempPercent = clamp((temp / maxHp) * 100, 0, 100);
  const hpFill = $("hp-bar-fill");
  const tempFill = $("hp-bar-temp");
  if (hpFill) hpFill.style.width = `${hpPercent}%`;
  if (tempFill) tempFill.style.width = `${tempPercent}%`;
  setText("hp-bar-label", `${current} / ${maxHp}${temp ? ` (+${temp})` : ""}`);

  const hitDie = CLASS_INFO[classKey()]?.hitDie || "d8";
  const hdAvailable = clamp(numberValue("hit_dice_available", 0), 0, level());
  setValue("hit_dice_available", hdAvailable);
  setText("hd-bar-label", `${level()}${hitDie} (${hdAvailable} / ${level()})`);
  setHtml("hd-pips-container", Array.from({ length: level() }, (_, index) => `<span class="hd-pip ${index < hdAvailable ? "filled" : ""}"></span>`).join(""));

  const cdMax = Math.max(1, proficiencyBonus());
  const cdAvailable = clamp(numberValue("channel_divinity_available", 0), 0, cdMax);
  setValue("channel_divinity_available", cdAvailable);
  setHtml("cd-pips-container", Array.from({ length: cdMax }, (_, index) => `<span class="cd-pip ${index < cdAvailable ? "filled" : ""}"></span>`).join(""));
}

function renderProficiencies() {
  const info = CLASS_INFO[classKey()] || {};
  let armor = [...(info.armor || [])];
  if (classKey() === "cleric" && key(textValue("domain")).includes("life") && !armor.includes("Heavy")) armor.push("Heavy");
  setHtml("armor-proficiencies", armor.length ? armor.map((item) => `<tr><td>${esc(item)}</td></tr>`).join("") : `<tr><td>No armor proficiencies</td></tr>`);
  setHtml("weapon-proficiencies", (info.weapons || []).map((item) => `<tr><td>${esc(item)}</td></tr>`).join("") || `<tr><td>No weapon proficiencies</td></tr>`);
}

async function loadEquipmentLibrary() {
  if (equipmentLibrary.length) {
    renderEquipmentResults();
    return;
  }
  setText("equipment-library-status", "Loading equipment...");
  try {
    const cached = localStorage.getItem(EQUIPMENT_CACHE_KEY);
    if (cached) equipmentLibrary = JSON.parse(cached).map(normalizeItem);
  } catch {
    equipmentLibrary = [];
  }
  try {
    const response = await fetch("assets/data/equipment.json");
    if (response.ok) {
      const data = await response.json();
      const flattened = Object.entries(data).flatMap(([category, items]) => items.map((item) => ({ ...item, category: categoryLabel(category) })));
      equipmentLibrary = mergeByName([...equipmentLibrary, ...flattened.map(normalizeItem)]);
    }
  } catch (error) {
    console.warn("Equipment data load failed", error);
  }
  setText("equipment-library-status", `${equipmentLibrary.length} items loaded.`);
  renderEquipmentResults();
}

function categoryLabel(category) {
  return String(category || "Other").replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());
}

function mergeByName(items) {
  const seen = new Set();
  const result = [];
  for (const item of items) {
    const name = key(item.name);
    if (!name || seen.has(name)) continue;
    seen.add(name);
    result.push(item);
  }
  return result.sort((a, b) => String(a.name).localeCompare(String(b.name)));
}

function renderEquipmentResults() {
  const container = $("equipment-library-results");
  if (!container) return;
  const query = key(textValue("equipment-search-input"));
  const results = equipmentLibrary
    .filter((item) => !query || `${item.name} ${item.category} ${item.properties || ""}`.toLowerCase().includes(query))
    .slice(0, 60);
  if (!results.length) {
    container.innerHTML = `<div class="equipment-library-empty">No matching items.</div>`;
    return;
  }
  container.innerHTML = results
    .map((item) => `
      <article class="equipment-card">
        <div class="equipment-summary">
          <div class="equipment-header">
            <span class="equipment-name">${esc(item.name)}</span>
            <button class="equipment-action" type="button" data-add-equipment="${esc(item.name)}">Add</button>
          </div>
          <div class="equipment-specs">${esc(item.category)}${item.damage ? ` - ${esc(item.damage)} ${esc(item.damage_type || "")}` : ""}${armorBase(item) ? ` - AC ${armorBase(item)}` : ""}</div>
        </div>
      </article>`)
    .join("");
}

function addEquipmentItemByName(name) {
  const source = equipmentLibrary.find((item) => item.name === name) || equipmentLibrary[0];
  if (!source) return;
  inventoryItems.push(normalizeItem({ ...source, id: uid(), quantity: 1, equipped: false }));
  renderAll();
  scheduleSave();
}

function renderInventory() {
  const list = $("inventory-list");
  const empty = $("inventory-empty-state");
  if (!list) return;
  if (empty) empty.style.display = inventoryItems.length ? "none" : "";
  const groups = new Map();
  for (const item of inventoryItems) {
    const category = itemCategory(item);
    if (!groups.has(category)) groups.set(category, []);
    groups.get(category).push(item);
  }
  list.innerHTML = [...groups.entries()].map(([category, items]) => `
    <li class="inventory-category">
      <div class="inventory-category-header">${esc(category)}</div>
      ${items.map(renderInventoryItem).join("")}
    </li>`).join("");
  updateInventoryTotals();
  renderWeaponsGrid();
  renderArmorGrid();
}

function renderInventoryItem(item) {
  return `
    <div class="inventory-item" data-item-id="${esc(item.id)}">
      <div class="inventory-item-summary">
        <div class="inventory-item-main">
          <span class="inventory-item-name">${esc(item.name)}</span>
          <span class="inventory-item-qty">x${itemQuantity(item)}</span>
        </div>
        <div class="inventory-item-details">
          <span class="inventory-item-cost">${esc(item.cost || "")}</span>
          <span class="inventory-item-weight">${esc(item.weight || "")}</span>
        </div>
        <div class="inventory-item-actions">
          <label><input type="checkbox" data-item-equipped ${item.equipped ? "checked" : ""}> Equip</label>
          <button class="inventory-item-remove" type="button" data-remove-item="${esc(item.id)}">Remove</button>
        </div>
      </div>
      <div class="inventory-item-body open">
        <div class="inventory-item-field"><label>Qty</label><input type="number" min="1" data-item-qty value="${itemQuantity(item)}"></div>
        <div class="inventory-item-field"><label>Notes</label><textarea data-item-notes>${esc(item.notes || "")}</textarea></div>
      </div>
    </div>`;
}

function updateInventoryTotals() {
  let weight = 0;
  let cost = 0;
  for (const item of inventoryItems) {
    const qty = itemQuantity(item);
    weight += parseNumber(item.weight, 0) * qty;
    cost += parseCostGp(item.cost) * qty;
  }
  setText("equipment-total-weight", weight.toFixed(2).replace(/\.00$/, ""));
  setText("equipment-total-cost", cost.toFixed(2).replace(/\.00$/, ""));
}

function renderWeaponsGrid() {
  const rows = inventoryItems.filter((item) => item.equipped && isWeapon(item));
  if (!rows.length) {
    setHtml("weapons-grid", `<tr id="weapons-empty-state"><td colspan="5" style="text-align: center; padding: 1rem;">No weapons equipped. Add weapons from your equipment inventory.</td></tr>`);
    return;
  }
  setHtml("weapons-grid", rows.map((item) => `
    <tr>
      <td>${esc(item.name)}</td>
      <td>${fmtBonus(weaponToHit(item))}</td>
      <td>${esc(item.damage || item.damage_dice || "-")} ${esc(item.damage_type || "")}</td>
      <td>${esc(item.range || "-")}</td>
      <td>${esc(itemProperties(item).join(", ") || "-")}</td>
    </tr>`).join(""));
}

function weaponToHit(item) {
  const props = itemProperties(item).join(" ").toLowerCase();
  const ranged = /range|ammunition|thrown|bow|crossbow|sling/i.test(`${item.range || ""} ${item.name || ""} ${props}`);
  const finesse = props.includes("finesse");
  const ability = finesse ? Math.max(abilityMod("str"), abilityMod("dex")) : ranged ? abilityMod("dex") : abilityMod("str");
  return ability + proficiencyBonus() + magicBonus(item);
}

function renderArmorGrid() {
  const rows = inventoryItems.filter((item) => isArmor(item) || isShield(item));
  if (!rows.length) {
    setHtml("armor-grid", `<tr id="armor-empty-state"><td colspan="7" style="text-align: center; padding: 1rem;">No armor in inventory. Add armor from the Equipment tab.</td></tr>`);
    return;
  }
  setHtml("armor-grid", rows.map((item) => `
    <tr data-item-id="${esc(item.id)}">
      <td>${esc(item.name)}</td>
      <td>${isShield(item) ? "+2" : armorBase(item)}</td>
      <td>${esc(isShield(item) ? "Shield" : armorType(item))}</td>
      <td>${esc(item.material || "-")}</td>
      <td>${magicBonus(item) ? `+${magicBonus(item)}` : "-"}</td>
      <td>${/stealth/i.test(String(item.properties || "")) ? "Disadvantage" : "-"}</td>
      <td><input type="checkbox" data-item-equipped ${item.equipped ? "checked" : ""}></td>
    </tr>`).join(""));
}

function openCustomItemModal() {
  const modal = $("custom-item-modal");
  if (modal) modal.style.display = "flex";
}

function closeCustomItemModal() {
  const modal = $("custom-item-modal");
  if (modal) modal.style.display = "none";
}

function submitCustomItem() {
  const name = textValue("custom-item-name").trim();
  if (!name) {
    setCustomItemStatus("Item name is required.");
    return;
  }
  inventoryItems.push(normalizeItem({
    id: uid(),
    name,
    category: textValue("custom-item-category") || "",
    quantity: numberValue("custom-item-qty", 1),
    cost: textValue("custom-item-cost"),
    weight: textValue("custom-item-weight"),
    ac: textValue("custom-item-ac"),
    damage: textValue("custom-item-damage"),
    damage_type: textValue("custom-item-damage-type"),
    range: textValue("custom-item-range"),
    properties: textValue("custom-item-properties"),
    notes: textValue("custom-item-notes"),
  }));
  for (const id of ["custom-item-name", "custom-item-cost", "custom-item-weight", "custom-item-ac", "custom-item-damage", "custom-item-damage-type", "custom-item-range", "custom-item-properties", "custom-item-notes"]) setValue(id, "");
  setValue("custom-item-qty", 1);
  closeCustomItemModal();
  renderAll();
  scheduleSave();
}

function setCustomItemStatus(message) {
  const status = $("custom-item-fetch-status");
  if (!status) return;
  status.style.display = "block";
  status.textContent = message;
}

async function fetchCustomItemFromUrl() {
  setCustomItemStatus("URL import is now JavaScript-only. Browser CORS may block compendium pages; paste details manually if fetch fails.");
  const url = textValue("custom-item-url").trim();
  if (!url) return;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    const title = text.match(/<title[^>]*>([^<]+)/i)?.[1]?.replace(/\s+\|.*/, "").trim();
    if (title && !textValue("custom-item-name")) setValue("custom-item-name", title);
    setCustomItemStatus("Fetched page title. Review fields before adding.");
  } catch (error) {
    setCustomItemStatus(`Fetch failed: ${error.message}. Paste item details manually.`);
  }
}

async function loadSpellLibrary() {
  setText("spell-library-status", "Loading spells...");
  let spells = [];
  try {
    const cached = localStorage.getItem(SPELL_CACHE_KEY);
    if (cached) spells = JSON.parse(cached);
  } catch {
    spells = [];
  }
  if (!spells.length) {
    try {
      const response = await fetch("https://api.open5e.com/spells/?limit=1000");
      if (response.ok) {
        const payload = await response.json();
        spells = Array.isArray(payload.results) ? payload.results : [];
      }
    } catch (error) {
      console.warn("Open5e spell fetch failed", error);
    }
  }
  try {
    const response = await fetch("assets/data/spells.json");
    if (response.ok) {
      const payload = await response.json();
      spells = mergeSpells([...spells, ...(payload.LOCAL_SPELLS_FALLBACK || [])]);
    }
  } catch (error) {
    console.warn("Local spell fallback failed", error);
  }
  spellLibrary = sanitizeSpells(spells);
  spellMap = new Map(spellLibrary.map((spell) => [spell.slug, spell]));
  localStorage.setItem(SPELL_CACHE_KEY, JSON.stringify(spellLibrary));
  populateSpellClassFilter();
  ensureDomainSpells();
  setText("spell-library-status", `${spellLibrary.length} spells loaded.`);
  renderSpells();
  scheduleSave();
}

function mergeSpells(spells) {
  const seen = new Set();
  const result = [];
  for (const spell of spells) {
    const slug = slugify(spell.slug || spell.name);
    if (!slug || seen.has(slug)) continue;
    seen.add(slug);
    result.push(spell);
  }
  return result;
}

function sanitizeSpells(spells) {
  return spells.map((raw) => {
    const classes = parseSpellClasses(raw);
    const levelInt = Number.parseInt(raw.level_int ?? raw.level ?? 0, 10) || 0;
    const desc = Array.isArray(raw.desc) ? raw.desc.join("\n") : String(raw.desc || "");
    const higher = Array.isArray(raw.higher_level) ? raw.higher_level.join("\n") : String(raw.higher_level || "");
    const name = raw.name || "Unknown Spell";
    return {
      slug: slugify(raw.slug || name),
      name,
      level_int: levelInt,
      level_label: spellLevelLabel(levelInt),
      school: title(raw.school || ""),
      casting_time: raw.casting_time || "",
      range: raw.range || "",
      components: raw.components || "",
      material: raw.material || "",
      duration: raw.duration || "",
      ritual: Boolean(raw.ritual),
      concentration: Boolean(raw.concentration),
      classes,
      classes_display: classes.map(title),
      source: raw.document__title || raw.source || raw.document || "",
      description_html: paragraphs(desc) + (higher ? `<p class="spell-section-title">At Higher Levels</p>${paragraphs(higher)}` : ""),
      search_blob: `${name} ${classes.join(" ")} ${desc} ${higher} ${raw.school || ""}`.toLowerCase(),
    };
  }).filter((spell) => spell.slug && spell.classes.length).sort((a, b) => a.level_int - b.level_int || a.name.localeCompare(b.name));
}

function parseSpellClasses(raw) {
  const source = raw.dnd_class || raw.classes || raw.spell_lists || "";
  const parts = Array.isArray(source) ? source : String(source).split(/[,;/]+/);
  return [...new Set(parts.map((part) => key(part).replace(/^the /, "")).filter(Boolean))];
}

function slugify(value) {
  return key(value).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function title(value) {
  return String(value || "").replace(/[-_]/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());
}

function spellLevelLabel(value) {
  return value === 0 ? "Cantrip" : `Level ${value}`;
}

function paragraphs(text) {
  return String(text || "").split(/\n+/).filter(Boolean).map((line) => `<p>${esc(line)}</p>`).join("");
}

function populateSpellClassFilter() {
  const select = $("spell-class-filter");
  if (!select) return;
  const selected = select.value;
  const classes = [...new Set(spellLibrary.flatMap((spell) => spell.classes))].sort();
  select.innerHTML = `<option value="">Any class</option>${classes.map((cls) => `<option value="${esc(cls)}">${esc(title(cls))}</option>`).join("")}`;
  select.value = selected;
}

function renderSpells() {
  renderSpellResults();
  renderSpellbook();
  renderSpellSlots();
}

function renderSpellResults() {
  const container = $("spell-library-results");
  if (!container) return;
  const query = key(textValue("spell-search"));
  const levelFilter = textValue("spell-level-filter");
  const classFilter = key(textValue("spell-class-filter"));
  const maxLevel = maxSpellLevel();
  const activeClass = classKey();
  const preparedSet = new Set(preparedSpells.map((entry) => entry.slug));
  const results = spellLibrary.filter((spell) => {
    if (query && !spell.search_blob.includes(query)) return false;
    if (levelFilter !== "" && spell.level_int !== Number(levelFilter)) return false;
    if (classFilter && !spell.classes.includes(classFilter)) return false;
    if (!classFilter && CASTER_CLASSES.has(activeClass) && !spell.classes.includes(activeClass)) return false;
    return spell.level_int <= maxLevel;
  }).slice(0, 120);
  if (!results.length) {
    container.innerHTML = `<div class="spellbook-empty">No matching spells.</div>`;
    return;
  }
  container.innerHTML = results.map((spell) => `
    <details class="spell-card ${preparedSet.has(spell.slug) ? "selected" : ""}">
      <summary>
        <span class="spell-name">${esc(spell.name)}</span>
        <span class="spell-meta">${esc(spell.level_label)} - ${esc(spell.school)} - ${esc(spell.classes_display.join(", "))}</span>
      </summary>
      <div class="spell-body">
        <p><strong>Casting:</strong> ${esc(spell.casting_time)} | <strong>Range:</strong> ${esc(spell.range)} | <strong>Duration:</strong> ${esc(spell.duration)}</p>
        ${spell.description_html}
        <button type="button" class="equipment-action" data-spell-toggle="${esc(spell.slug)}">${preparedSet.has(spell.slug) ? "Remove" : "Add"}</button>
      </div>
    </details>`).join("");
}

function maxSpellLevel() {
  const slots = currentSlotTable();
  return Math.max(0, ...Object.keys(slots).map(Number));
}

function currentSlotTable() {
  const cls = classKey();
  const lvl = level();
  if (CASTER_CLASSES.has(cls)) return STANDARD_SLOT_TABLE[lvl] || {};
  if (HALF_CASTER_CLASSES.has(cls)) return STANDARD_SLOT_TABLE[Math.ceil(lvl / 2)] || {};
  if (PACT_CLASSES.has(cls)) return lvl >= 17 ? { 5: 4 } : lvl >= 11 ? { 5: 3 } : lvl >= 9 ? { 5: 2 } : lvl >= 7 ? { 4: 2 } : lvl >= 5 ? { 3: 2 } : lvl >= 3 ? { 2: 2 } : lvl >= 1 ? { 1: 1 } : {};
  return {};
}

function preparedLimit() {
  const cls = classKey();
  if (cls === "cleric" || cls === "druid") return Math.max(1, abilityMod(spellAbility()) + level());
  if (cls === "paladin") return Math.max(1, abilityMod(spellAbility()) + Math.floor(level() / 2));
  return preparedSpells.length;
}

function ensureDomainSpells() {
  if (classKey() !== "cleric") return;
  const domain = key(textValue("domain")).replace(/\s+domain$/, "");
  const table = DOMAIN_SPELLS[domain];
  if (!table) return;
  const slugs = new Set(preparedSpells.map((entry) => entry.slug));
  for (const [requiredLevel, spells] of Object.entries(table)) {
    if (level() < Number(requiredLevel)) continue;
    for (const slug of spells) {
      if (!slugs.has(slug)) {
        preparedSpells.push({ slug, is_domain_bonus: true });
        slugs.add(slug);
      }
    }
  }
  for (const entry of preparedSpells) {
    if (Object.values(table).flat().includes(entry.slug)) entry.is_domain_bonus = true;
  }
}

function renderSpellbook() {
  const levels = $("spellbook-levels");
  const empty = $("spellbook-empty-state");
  if (!levels) return;
  const spellEntries = preparedSpells.map((entry) => ({ entry, spell: spellMap.get(entry.slug) })).filter((item) => item.spell);
  const nonDomainCount = preparedSpells.filter((entry) => !entry.is_domain_bonus).length;
  setText("spellbook-prepared-count", `${nonDomainCount} / ${preparedLimit()}`);
  setText("prepared-calc-hint", classKey() === "cleric" ? `Prepared limit: Wisdom modifier (${fmtBonus(abilityMod("wis"))}) + cleric level (${level()}). Domain spells do not count.` : "");
  if (empty) empty.style.display = spellEntries.length ? "none" : "";
  if (!spellEntries.length) {
    levels.innerHTML = "";
    return;
  }
  const grouped = new Map();
  for (const item of spellEntries) {
    const levelKey = item.spell.level_int;
    if (!grouped.has(levelKey)) grouped.set(levelKey, []);
    grouped.get(levelKey).push(item);
  }
  levels.innerHTML = [...grouped.entries()].sort((a, b) => a[0] - b[0]).map(([spellLevel, items]) => `
    <section class="spellbook-level">
      <header><h3>${esc(spellLevelLabel(spellLevel))}</h3><span class="spell-level-slots">${slotText(spellLevel)}</span></header>
      <ul>${items.map(({ entry, spell }) => renderSpellbookSpell(entry, spell)).join("")}</ul>
    </section>`).join("");
}

function renderSpellbookSpell(entry, spell) {
  return `
    <li class="spellbook-spell">
      <details class="spellbook-details">
        <summary>
          <span class="spellbook-summary-main">
            <span class="spellbook-name">${esc(spell.name)}${entry.is_domain_bonus ? " (Domain)" : ""}</span>
            <span class="spellbook-meta">${esc(spell.level_label)} - ${esc(spell.school)}</span>
          </span>
          <span class="spellbook-actions">
            ${spell.level_int > 0 ? `<button type="button" class="spellbook-cast" data-cast-spell="${esc(spell.slug)}">Cast</button>` : ""}
            ${entry.is_domain_bonus ? "" : `<button type="button" class="spellbook-remove" data-spell-toggle="${esc(spell.slug)}">Remove</button>`}
          </span>
        </summary>
        <div class="spellbook-body">${spell.description_html || `<p class="spellbook-description-empty">No description available.</p>`}</div>
      </details>
    </li>`;
}

function slotText(spellLevel) {
  if (spellLevel === 0) return "At will";
  const total = currentSlotTable()[spellLevel] || 0;
  const used = Number(spellSlotsUsed[spellLevel] || 0);
  return `${Math.max(0, total - used)} / ${total} available`;
}

function renderSpellSlots() {
  const container = $("spellbook-slots-summary");
  if (!container) return;
  const slots = currentSlotTable();
  if (!Object.keys(slots).length) {
    container.innerHTML = `<div class="spell-slots-empty">No spell slots for the selected class and level.</div>`;
    return;
  }
  container.innerHTML = Object.entries(slots).map(([spellLevel, total]) => {
    const used = Number(spellSlotsUsed[spellLevel] || 0);
    return `<div class="slot-tracker-item">
      <span class="slot-tracker-label">Level ${spellLevel}</span>
      <span class="slot-tracker-value">${Math.max(0, total - used)} / ${total}</span>
      <button type="button" data-slot-delta="${spellLevel}:-1">-</button>
      <button type="button" data-slot-delta="${spellLevel}:1">+</button>
    </div>`;
  }).join("");
}

function togglePreparedSpell(slug) {
  const existing = preparedSpells.find((entry) => entry.slug === slug);
  if (existing) {
    if (!existing.is_domain_bonus) preparedSpells = preparedSpells.filter((entry) => entry.slug !== slug);
  } else {
    preparedSpells.push({ slug, is_domain_bonus: false });
  }
  renderSpells();
  scheduleSave();
}

function castSpell(slug) {
  const spell = spellMap.get(slug);
  if (!spell || spell.level_int < 1) return;
  const total = currentSlotTable()[spell.level_int] || 0;
  const used = Number(spellSlotsUsed[spell.level_int] || 0);
  if (used >= total) return;
  spellSlotsUsed[spell.level_int] = used + 1;
  renderSpells();
  scheduleSave();
}

function resetSpellSlots() {
  spellSlotsUsed = {};
  setValue("current_hp", numberValue("max_hp", 8));
  setValue("temp_hp", 0);
  setValue("hit_dice_available", level());
  setValue("channel_divinity_available", proficiencyBonus());
  renderAll();
  scheduleSave();
}

function renderClassFeatures() {
  const container = $("class-features-container");
  if (!container) return;
  const groups = [];
  const cls = classKey();
  const lvl = level();
  for (const [required, features] of Object.entries(CLASS_FEATURES[cls] || {})) {
    if (lvl >= Number(required)) groups.push([required, features]);
  }
  const domain = key(textValue("domain")).replace(/\s+domain$/, "");
  for (const [required, features] of Object.entries(DOMAIN_FEATURES[domain] || {})) {
    if (lvl >= Number(required)) groups.push([required, features.map((feature) => [`${title(domain)} Domain: ${feature[0]}`, feature[1]])]);
  }
  if (!groups.length) {
    container.innerHTML = `<div class="class-features-empty">No class features available for the current class and level yet.</div>`;
    return;
  }
  container.innerHTML = groups.sort((a, b) => Number(a[0]) - Number(b[0])).map(([required, features]) => `
    <section class="class-feature-level">
      <div class="class-feature-level-header"><span class="level-indicator">Level ${esc(required)}</span></div>
      <div class="class-feature-level-content expanded">
        ${features.map(([name, description]) => `<article class="class-feature-item"><div class="class-feature-name">${esc(name)}</div><div class="class-feature-description">${esc(description)}</div></article>`).join("")}
      </div>
    </section>`).join("");
}

function addFeat() {
  const name = textValue("feat-name-input").trim();
  if (!name) return;
  feats.push({ id: uid(), name, level: numberValue("feat-level-input", level()), description: textValue("feat-description-input") });
  setValue("feat-name-input", "");
  setValue("feat-description-input", "");
  renderFeats();
  scheduleSave();
}

function renderFeats() {
  const container = $("feats-list");
  if (!container) return;
  if (!feats.length) {
    container.innerHTML = `<div class="feats-empty">No feats or custom abilities added yet.</div>`;
    return;
  }
  container.innerHTML = feats.map((feat) => `
    <article class="feat-card">
      <div class="feat-card-header">
        <div class="feat-info"><span class="feat-name">${esc(feat.name)}</span><span class="feat-level">Level ${esc(feat.level || 1)}</span></div>
        <div class="feat-actions"><button class="feat-action-btn remove" type="button" data-remove-feat="${esc(feat.id)}">Remove</button></div>
      </div>
      <div class="feat-description">${esc(feat.description || "")}</div>
    </article>`).join("");
}

async function exportCharacter() {
  saveCharacter({ quiet: true });
  const data = collectCharacterData();
  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: exportFilename(data), content: data }),
    });
    if (!response.ok) throw new Error(`Export API returned ${response.status}`);
    const payload = await response.json();
    setStorageMessage(`Exported ${payload.filename || "character JSON"}.`);
  } catch (error) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    const safeName = slugify(data.identity.name || "character") || "character";
    link.href = URL.createObjectURL(blob);
    link.download = `${safeName}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
    setStorageMessage(`Backend export unavailable, downloaded JSON locally. ${error.message}`);
  }
}

function exportFilename(data) {
  const name = slugify(data.identity?.name || "character").replace(/-/g, "_") || "character";
  const cls = slugify(data.identity?.class || "adventurer").replace(/-/g, "_") || "adventurer";
  const stamp = new Date().toISOString().replace(/[-:]/g, "").slice(0, 13).replace("T", "_");
  return `${name}_${cls}_lvl${data.level || 1}_${stamp}.json`;
}

function importCharacter(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      populateForm(JSON.parse(reader.result));
      saveCharacter();
      setStorageMessage("Imported character JSON.");
    } catch (error) {
      setStorageMessage(`Import failed: ${error.message}`);
    }
  };
  reader.readAsText(file);
}

function resetCharacter() {
  if (!window.confirm("Reset the current character sheet?")) return;
  localStorage.removeItem(LOCAL_STORAGE_KEY);
  populateForm(defaultState());
  saveCharacter();
}

function showStorageInfo() {
  const characterBytes = new Blob([localStorage.getItem(LOCAL_STORAGE_KEY) || ""]).size;
  const spellBytes = new Blob([localStorage.getItem(SPELL_CACHE_KEY) || ""]).size;
  setStorageMessage(`Local storage: character ${characterBytes} bytes, spells ${spellBytes} bytes.`);
}

function cleanupExports() {
  localStorage.removeItem(SPELL_CACHE_KEY);
  setStorageMessage("Cleared cached spell data. Saved characters and exports were left alone.");
}

function setStorageMessage(message) {
  setText("storage-message", message);
}

async function populateCharacterSwitcher() {
  const select = $("character-switcher");
  if (!select) return;
  select.innerHTML = `<option value="">Current browser save</option>`;
  try {
    const response = await fetch("/api/exports");
    if (!response.ok) return;
    const payload = await response.json();
    for (const item of payload.exports || []) {
      const option = document.createElement("option");
      option.value = item.filename;
      option.textContent = item.filename.replace(/\.json$/i, "");
      select.appendChild(option);
    }
  } catch {
    // Static-file mode can skip export listing.
  }
}

async function loadSelectedExport(filename) {
  if (!filename) return;
  const response = await fetch(`/exports/${encodeURIComponent(filename)}`);
  if (!response.ok) return;
  populateForm(await response.json());
  saveCharacter();
}

function handleAdjustButton(button) {
  const target = button.dataset.adjustTarget;
  if (!target) return;
  let next = numberValue(target, 0);
  if (button.dataset.adjustSet !== undefined) next = Number(button.dataset.adjustSet);
  if (button.dataset.adjustSetId) next = numberValue(button.dataset.adjustSetId, next);
  if (button.dataset.adjustDelta) next += Number(button.dataset.adjustDelta);
  if (button.dataset.adjustMaxId) next = Math.min(next, numberValue(button.dataset.adjustMaxId, next));
  if (button.dataset.adjustMaxBy === "proficiency") next = Math.min(next, proficiencyBonus());
  if (button.dataset.adjustMin !== undefined) next = Math.max(next, Number(button.dataset.adjustMin));
  setValue(target, next);
  renderAll();
  scheduleSave();
}

function handleCurrencyButton(button) {
  const coin = button.dataset.currency;
  const amount = Number(button.dataset.amount || 0);
  if (!coin) return;
  setValue(`currency-${coin}`, Math.max(0, numberValue(`currency-${coin}`, 0) + amount));
  scheduleSave();
}

function renderAll() {
  ensureDomainSpells();
  updateCalculations();
  renderInventory();
  renderSpells();
  renderClassFeatures();
  renderFeats();
  updateHeader();
}

function updateHeader() {
  const name = textValue("name") || "Unnamed Hero";
  const cls = textValue("class") || "Adventurer";
  const race = textValue("race") || "";
  setText("character-header-name", name);
  setText("character-header-summary", `${race} ${cls} - Level ${level()}`.trim());
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = `tab-${button.dataset.tab}`;
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab === button));
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === targetId));
    });
  });

  document.querySelectorAll("[data-character-input]").forEach((input) => {
    input.addEventListener("input", () => {
      renderAll();
      scheduleSave();
    });
    input.addEventListener("change", () => {
      renderAll();
      scheduleSave();
    });
  });

  $("equipment-load-btn")?.addEventListener("click", loadEquipmentLibrary);
  $("equipment-add-btn")?.addEventListener("click", () => addEquipmentItemByName(equipmentLibrary[0]?.name));
  $("equipment-custom-btn")?.addEventListener("click", openCustomItemModal);
  $("equipment-search-input")?.addEventListener("input", renderEquipmentResults);
  $("spells-load-btn")?.addEventListener("click", loadSpellLibrary);
  $("long-rest-spell-btn")?.addEventListener("click", resetSpellSlots);
  $("long-rest-btn")?.addEventListener("click", resetSpellSlots);
  $("spell-search")?.addEventListener("input", renderSpellResults);
  $("spell-level-filter")?.addEventListener("change", renderSpellResults);
  $("spell-class-filter")?.addEventListener("change", renderSpellResults);
  $("feat-add-btn")?.addEventListener("click", addFeat);
  $("save-btn")?.addEventListener("click", () => saveCharacter());
  $("reset-btn")?.addEventListener("click", resetCharacter);
  $("export-btn")?.addEventListener("click", exportCharacter);
  $("import-file")?.addEventListener("change", (event) => importCharacter(event.target.files?.[0]));
  $("storage-info-btn")?.addEventListener("click", showStorageInfo);
  $("cleanup-btn")?.addEventListener("click", cleanupExports);
  $("reset-channel-divinity")?.addEventListener("click", () => {
    setValue("channel_divinity_available", proficiencyBonus());
    renderAll();
    scheduleSave();
  });
  $("character-switcher")?.addEventListener("change", (event) => loadSelectedExport(event.target.value));
  $("custom-item-close")?.addEventListener("click", closeCustomItemModal);
  $("custom-item-cancel")?.addEventListener("click", closeCustomItemModal);
  $("custom-item-add")?.addEventListener("click", submitCustomItem);
  $("custom-item-fetch-btn")?.addEventListener("click", fetchCustomItemFromUrl);

  document.addEventListener("click", (event) => {
    const addButton = event.target.closest("[data-add-equipment]");
    if (addButton) addEquipmentItemByName(addButton.dataset.addEquipment);
    const removeButton = event.target.closest("[data-remove-item]");
    if (removeButton) {
      inventoryItems = inventoryItems.filter((item) => item.id !== removeButton.dataset.removeItem);
      renderAll();
      scheduleSave();
    }
    const spellButton = event.target.closest("[data-spell-toggle]");
    if (spellButton) togglePreparedSpell(spellButton.dataset.spellToggle);
    const castButton = event.target.closest("[data-cast-spell]");
    if (castButton) castSpell(castButton.dataset.castSpell);
    const featButton = event.target.closest("[data-remove-feat]");
    if (featButton) {
      feats = feats.filter((feat) => feat.id !== featButton.dataset.removeFeat);
      renderFeats();
      scheduleSave();
    }
    const adjustButton = event.target.closest("[data-adjust-target]");
    if (adjustButton) handleAdjustButton(adjustButton);
    const currencyButton = event.target.closest(".currency-btn");
    if (currencyButton) handleCurrencyButton(currencyButton);
    const slotButton = event.target.closest("[data-slot-delta]");
    if (slotButton) {
      const [spellLevel, delta] = slotButton.dataset.slotDelta.split(":").map(Number);
      const max = currentSlotTable()[spellLevel] || 0;
      spellSlotsUsed[spellLevel] = clamp(Number(spellSlotsUsed[spellLevel] || 0) + delta, 0, max);
      renderSpells();
      scheduleSave();
    }
  });

  document.addEventListener("change", (event) => {
    const itemRoot = event.target.closest("[data-item-id]");
    if (!itemRoot) return;
    const item = inventoryItems.find((entry) => entry.id === itemRoot.dataset.itemId);
    if (!item) return;
    if (event.target.matches("[data-item-equipped]")) item.equipped = event.target.checked;
    if (event.target.matches("[data-item-qty]")) item.quantity = Math.max(1, Number(event.target.value) || 1);
    if (event.target.matches("[data-item-notes]")) item.notes = event.target.value;
    renderAll();
    scheduleSave();
  });

  window.setupAutoExportDirectory = async (pickerMethod) => {
    if (!pickerMethod) return null;
    try {
      return await pickerMethod();
    } catch {
      return null;
    }
  };
}

async function init() {
  bindEvents();
  loadInitialState();
  await loadEquipmentLibrary();
  try {
    const cached = localStorage.getItem(SPELL_CACHE_KEY);
    if (cached) {
      spellLibrary = JSON.parse(cached);
      spellMap = new Map(spellLibrary.map((spell) => [spell.slug, spell]));
      populateSpellClassFilter();
      renderSpells();
    }
  } catch {
    // Spell cache is optional.
  }
  populateCharacterSwitcher();
  setSavingMessage("Ready", "fading");
}

document.addEventListener("DOMContentLoaded", init);
