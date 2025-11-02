// Spell Manager for PySheet D&D Character Sheet
// Manages spell selection, filtering, and display

class SpellManager {
  constructor() {
    this.chosenSpells = [];
    this.currentSpellSlots = [];
    this.activeDetailSpell = null;
    this.currentClassFilter = 'all';
    this.currentLevelFilter = 'all';
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }

  init() {
    this.loadChosenSpells();
    this.renderAvailableSpells();
    this.renderChosenSpells();
    this.updateSpellSlots();
    this.attachEventListeners();
  }

  attachEventListeners() {
    // Class filter
    const classFilter = document.getElementById('spell-class-filter');
    if (classFilter) {
      classFilter.addEventListener('change', (e) => {
        this.currentClassFilter = e.target.value;
        this.renderAvailableSpells();
      });
    }

    // Level filter
    const levelFilter = document.getElementById('spell-level-filter');
    if (levelFilter) {
      levelFilter.addEventListener('change', (e) => {
        this.currentLevelFilter = e.target.value;
        this.renderAvailableSpells();
      });
    }

    // Listen for level changes to update spell slots
    const levelInput = document.getElementById('level');
    if (levelInput) {
      levelInput.addEventListener('input', () => {
        this.updateSpellSlots();
      });
      levelInput.addEventListener('change', () => {
        this.updateSpellSlots();
      });
    }

    // Close modal when clicking outside
    const modal = document.getElementById('spell-detail-modal');
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.hideSpellDetail();
        }
      });
    }
  }

  getFilteredSpells() {
    const spells = Object.values(SPELL_DATABASE);
    return spells.filter(spell => {
      // Filter by class
      if (this.currentClassFilter !== 'all') {
        if (!spell.classes.includes(this.currentClassFilter)) {
          return false;
        }
      }
      
      // Filter by level
      if (this.currentLevelFilter !== 'all') {
        const filterLevel = parseInt(this.currentLevelFilter);
        if (spell.level !== filterLevel) {
          return false;
        }
      }
      
      return true;
    }).sort((a, b) => {
      // Sort by level, then by name
      if (a.level !== b.level) {
        return a.level - b.level;
      }
      return a.name.localeCompare(b.name);
    });
  }

  renderAvailableSpells() {
    const container = document.getElementById('available-spells-list');
    if (!container) return;

    const filteredSpells = this.getFilteredSpells();
    
    if (filteredSpells.length === 0) {
      container.innerHTML = '<p class="empty-message">No spells match the current filters.</p>';
      return;
    }

    let currentLevel = -1;
    let html = '';

    filteredSpells.forEach(spell => {
      const spellId = this.getSpellId(spell.name);
      const isChosen = this.chosenSpells.includes(spellId);
      
      // Add level header
      if (spell.level !== currentLevel) {
        currentLevel = spell.level;
        const levelLabel = spell.level === 0 ? 'Cantrips' : `Level ${spell.level}`;
        html += `<div class="spell-level-header">${levelLabel}</div>`;
      }

      html += `
        <div class="spell-item ${isChosen ? 'chosen' : ''}" data-spell-id="${spellId}">
          <div class="spell-item-header">
            <span class="spell-name">${spell.name}</span>
            <button class="spell-add-btn ${isChosen ? 'remove' : 'add'}" 
                    data-spell-id="${spellId}"
                    title="${isChosen ? 'Remove from your spells' : 'Add to your spells'}">
              ${isChosen ? '−' : '+'}
            </button>
          </div>
          <div class="spell-item-meta">${spell.school} • ${spell.classes.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')}</div>
        </div>
      `;
    });

    container.innerHTML = html;

    // Attach click handlers
    container.querySelectorAll('.spell-item').forEach(item => {
      const spellId = item.dataset.spellId;
      const spell = this.getSpellById(spellId);
      
      // Click on spell item (but not button) to show details
      item.addEventListener('click', (e) => {
        if (!e.target.classList.contains('spell-add-btn')) {
          this.toggleSpellDetail(spell);
        }
      });
    });

    // Attach add/remove button handlers
    container.querySelectorAll('.spell-add-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const spellId = btn.dataset.spellId;
        this.toggleSpell(spellId);
      });
    });
  }

  renderChosenSpells() {
    const container = document.getElementById('chosen-spells-list');
    if (!container) return;

    if (this.chosenSpells.length === 0) {
      container.innerHTML = '<p class="empty-message">No spells chosen yet. Select spells from the left panel.</p>';
      return;
    }

    const spells = this.chosenSpells.map(id => this.getSpellById(id)).filter(s => s);
    spells.sort((a, b) => {
      if (a.level !== b.level) {
        return a.level - b.level;
      }
      return a.name.localeCompare(b.name);
    });

    let currentLevel = -1;
    let html = '';

    spells.forEach(spell => {
      const spellId = this.getSpellId(spell.name);
      
      // Add level header
      if (spell.level !== currentLevel) {
        currentLevel = spell.level;
        const levelLabel = spell.level === 0 ? 'Cantrips' : `Level ${spell.level}`;
        html += `<div class="spell-level-header">${levelLabel}</div>`;
      }

      html += `
        <div class="spell-item chosen" data-spell-id="${spellId}">
          <div class="spell-item-header">
            <span class="spell-name">${spell.name}</span>
            <button class="spell-remove-btn" data-spell-id="${spellId}" title="Remove from your spells">×</button>
          </div>
          <div class="spell-item-meta">${spell.school} • ${spell.castingTime}</div>
        </div>
      `;
    });

    container.innerHTML = html;

    // Attach click handlers
    container.querySelectorAll('.spell-item').forEach(item => {
      const spellId = item.dataset.spellId;
      const spell = this.getSpellById(spellId);
      
      // Click on spell item to show details
      item.addEventListener('click', (e) => {
        if (!e.target.classList.contains('spell-remove-btn')) {
          this.toggleSpellDetail(spell);
        }
      });
    });

    // Attach remove button handlers
    container.querySelectorAll('.spell-remove-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const spellId = btn.dataset.spellId;
        this.toggleSpell(spellId);
      });
    });
  }

  updateSpellSlots() {
    const container = document.getElementById('spell-slots-container');
    if (!container) return;

    const levelInput = document.getElementById('level');
    const characterLevel = levelInput ? parseInt(levelInput.value) || 1 : 1;
    
    const maxSlots = SPELL_SLOTS_BY_LEVEL[characterLevel] || SPELL_SLOTS_BY_LEVEL[1];
    
    // Initialize current slots if needed
    if (this.currentSpellSlots.length === 0) {
      this.currentSpellSlots = [...maxSlots];
      this.loadSpellSlots();
    }
    
    // Adjust array size if character level changed
    while (this.currentSpellSlots.length < 9) {
      this.currentSpellSlots.push(0);
    }

    let html = '';
    for (let i = 0; i < 9; i++) {
      const max = maxSlots[i];
      const current = Math.min(this.currentSpellSlots[i] || max, max);
      
      if (max > 0) {
        html += `
          <div class="spell-slot-level">
            <div class="spell-slot-header">Level ${i + 1}</div>
            <div class="spell-slot-tracker">
              <button class="spell-slot-btn decrease" data-level="${i}" ${current === 0 ? 'disabled' : ''}>−</button>
              <span class="spell-slot-count">${current} / ${max}</span>
              <button class="spell-slot-btn increase" data-level="${i}" ${current >= max ? 'disabled' : ''}>+</button>
            </div>
            <div class="spell-slot-dots">
              ${this.renderSlotDots(current, max)}
            </div>
          </div>
        `;
      }
    }

    container.innerHTML = html;

    // Attach event listeners
    container.querySelectorAll('.spell-slot-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const level = parseInt(btn.dataset.level);
        const isIncrease = btn.classList.contains('increase');
        this.adjustSpellSlot(level, isIncrease ? 1 : -1);
      });
    });
  }

  renderSlotDots(current, max) {
    let html = '';
    for (let i = 0; i < max; i++) {
      html += `<span class="spell-slot-dot ${i < current ? 'filled' : ''}"></span>`;
    }
    return html;
  }

  adjustSpellSlot(level, delta) {
    const levelInput = document.getElementById('level');
    const characterLevel = levelInput ? parseInt(levelInput.value) || 1 : 1;
    const maxSlots = SPELL_SLOTS_BY_LEVEL[characterLevel] || SPELL_SLOTS_BY_LEVEL[1];
    
    const newValue = this.currentSpellSlots[level] + delta;
    const max = maxSlots[level];
    
    if (newValue >= 0 && newValue <= max) {
      this.currentSpellSlots[level] = newValue;
      this.saveSpellSlots();
      this.updateSpellSlots();
    }
  }

  toggleSpell(spellId) {
    const index = this.chosenSpells.indexOf(spellId);
    if (index > -1) {
      this.chosenSpells.splice(index, 1);
    } else {
      this.chosenSpells.push(spellId);
    }
    
    this.saveChosenSpells();
    this.renderAvailableSpells();
    this.renderChosenSpells();
  }

  toggleSpellDetail(spell) {
    if (this.activeDetailSpell === spell.name) {
      this.hideSpellDetail();
    } else {
      this.showSpellDetail(spell);
    }
  }

  showSpellDetail(spell) {
    this.activeDetailSpell = spell.name;
    
    const modal = document.getElementById('spell-detail-modal');
    if (!modal) return;

    document.getElementById('spell-modal-name').textContent = spell.name;
    document.getElementById('spell-modal-level').textContent = spell.level === 0 ? 'Cantrip' : `Level ${spell.level}`;
    document.getElementById('spell-modal-school').textContent = spell.school;
    document.getElementById('spell-modal-casting-time').textContent = spell.castingTime;
    document.getElementById('spell-modal-range').textContent = spell.range;
    document.getElementById('spell-modal-components').textContent = spell.components;
    document.getElementById('spell-modal-duration').textContent = spell.duration;
    document.getElementById('spell-modal-description').textContent = spell.description;

    modal.style.display = 'flex';
  }

  hideSpellDetail() {
    this.activeDetailSpell = null;
    const modal = document.getElementById('spell-detail-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  }

  getSpellId(spellName) {
    return spellName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  }

  getSpellById(spellId) {
    return SPELL_DATABASE[spellId];
  }

  saveChosenSpells() {
    try {
      localStorage.setItem('pysheet.spells.chosen', JSON.stringify(this.chosenSpells));
    } catch (e) {
      console.error('Failed to save chosen spells:', e);
    }
  }

  loadChosenSpells() {
    try {
      const stored = localStorage.getItem('pysheet.spells.chosen');
      if (stored) {
        this.chosenSpells = JSON.parse(stored);
      }
    } catch (e) {
      console.error('Failed to load chosen spells:', e);
      this.chosenSpells = [];
    }
  }

  saveSpellSlots() {
    try {
      localStorage.setItem('pysheet.spells.slots', JSON.stringify(this.currentSpellSlots));
    } catch (e) {
      console.error('Failed to save spell slots:', e);
    }
  }

  loadSpellSlots() {
    try {
      const stored = localStorage.getItem('pysheet.spells.slots');
      if (stored) {
        const slots = JSON.parse(stored);
        // Validate and use stored slots
        if (Array.isArray(slots) && slots.length === 9) {
          this.currentSpellSlots = slots;
        }
      }
    } catch (e) {
      console.error('Failed to load spell slots:', e);
    }
  }
}

// Initialize spell manager when document is ready
let spellManager;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    spellManager = new SpellManager();
  });
} else {
  spellManager = new SpellManager();
}
