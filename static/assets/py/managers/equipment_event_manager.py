"""
Event Listener Module - Centralized event handling for D&D Character Sheet.

Architecture Pattern:
    User Action → DOM Event → Event Listener → Manager Method → Data Update → GUI Redraw

Design Principles:
1. Thin coordination layer - just routes events to managers
2. No business logic here - managers own their domain logic
3. Serializable actions - each event maps to one manager method call
4. Clean flow - no circular dependencies or race conditions

Event Flow:
    1. User clicks bonus spinner
    2. DOM fires 'change' event
    3. EventListener.on_bonus_change() extracts event data
    4. Calls armor_manager.set_armor_bonus(item_id, value)
    5. armor_manager updates data
    6. inventory_manager.redraw_armor_items() updates UI
"""

from typing import Optional

try:
    from js import console, document
    from pyodide.ffi import create_proxy
except ImportError:
    # Mock for testing environments
    class _MockConsole:
        @staticmethod
        def log(*args): pass
        @staticmethod
        def warn(*args): pass
        @staticmethod
        def error(*args): pass
    
    console = _MockConsole()
    document = None
    create_proxy = None

# Try to import armor_manager at module level
try:
    from . import armor_manager
    ARMOR_MANAGER_AVAILABLE = True
except ImportError as e:
    console.warn(f"[EVENT-LISTENER-INIT] armor_manager import failed: {e}")
    armor_manager = None
    ARMOR_MANAGER_AVAILABLE = False

# Global registry for event proxies (prevents garbage collection)
_EVENT_PROXIES = []


class EquipmentEventListener:
    """Centralized event listener for equipment/inventory events."""
    
    def __init__(self, inventory_manager):
        """
        Initialize event listener with manager reference.
        
        Args:
            inventory_manager: The inventory manager instance to route events to
        """
        self.inventory_manager = inventory_manager
        self._is_updating = False  # Flag to prevent event loops during programmatic updates
        console.log("[EVENT-LISTENER] Initialized")
    
    # === Event Registration === 
    
    def register_all_handlers(self):
        """Register all DOM event handlers for inventory items."""
        global _EVENT_PROXIES
        
        console.log("[EVENT-LISTENER] Registering all handlers")
        
        # Clear old proxies to prevent memory leaks
        # When we use innerHTML, old DOM elements are destroyed but proxies remain in memory
        old_count = len(_EVENT_PROXIES)
        _EVENT_PROXIES = []
        if old_count > 0:
            console.log(f"[EVENT-LISTENER] Cleared {old_count} old proxies")
        
        inventory_list = document.getElementById("inventory-list")
        if not inventory_list:
            console.log("[EVENT-LISTENER] inventory-list not found, skipping")
            return
        
        # Register each event type
        self._register_toggle_handlers(inventory_list)
        self._register_remove_handlers(inventory_list)
        self._register_qty_handlers(inventory_list)
        self._register_category_handlers(inventory_list)
        self._register_bonus_handlers(inventory_list)
        self._register_equipped_handlers(inventory_list)
        self._register_custom_property_handlers(inventory_list)
        
        console.log(f"[EVENT-LISTENER] Registered {len(_EVENT_PROXIES)} new handlers")
    
    # === Specific Event Registration Methods ===
    
    def _register_bonus_handlers(self, container):
        """Register bonus change handlers (armor/weapon magical bonuses)."""
        bonus_inputs = container.querySelectorAll("[data-item-bonus]")
        console.log(f"[EVENT-LISTENER] Registering {len(bonus_inputs)} bonus handlers")
        
        for bonus_input in bonus_inputs:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-bonus")
                    if item_id:
                        self.on_bonus_change(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            bonus_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _register_toggle_handlers(self, container):
        """Register item expand/collapse toggle handlers."""
        toggles = container.querySelectorAll("[data-toggle-item]")
        
        for toggle in toggles:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-toggle-item")
                    if not item_id:
                        parent = event.target.parentElement
                        while parent and not item_id:
                            item_id = parent.getAttribute("data-toggle-item")
                            parent = parent.parentElement
                    if item_id:
                        self.on_toggle_item(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            toggle.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _register_remove_handlers(self, container):
        """Register item removal handlers."""
        removes = container.querySelectorAll("[data-remove-item]")
        
        for remove_btn in removes:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-remove-item")
                    if item_id:
                        self.on_remove_item(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            remove_btn.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _register_qty_handlers(self, container):
        """Register quantity change handlers."""
        qty_inputs = container.querySelectorAll("[data-item-qty]")
        
        for qty_input in qty_inputs:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-qty")
                    if item_id:
                        self.on_qty_change(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            qty_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _register_category_handlers(self, container):
        """Register category change handlers."""
        cat_selects = container.querySelectorAll("[data-item-category]")
        
        for cat_select in cat_selects:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-category")
                    if item_id:
                        self.on_category_change(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            cat_select.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _register_equipped_handlers(self, container):
        """Register equipped checkbox handlers."""
        checkboxes = container.querySelectorAll("[data-item-equipped]")
        
        for checkbox in checkboxes:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-equipped")
                    if item_id:
                        self.on_equipped_toggle(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            checkbox.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _register_custom_property_handlers(self, container):
        """Register handlers for various custom property inputs."""
        # AC modifiers
        ac_mod_inputs = container.querySelectorAll("[data-item-ac-mod]")
        for ac_input in ac_mod_inputs:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-ac-mod")
                    if item_id:
                        self.on_modifier_change(event, item_id, "ac_modifier")
                return handler
            
            proxy = create_proxy(make_handler())
            ac_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Saves modifiers
        saves_mod_inputs = container.querySelectorAll("[data-item-saves-mod]")
        for saves_input in saves_mod_inputs:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-saves-mod")
                    if item_id:
                        self.on_modifier_change(event, item_id, "saves_modifier")
                return handler
            
            proxy = create_proxy(make_handler())
            saves_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Armor-only checkboxes
        armor_only_checkboxes = container.querySelectorAll("[data-item-armor-only]")
        for checkbox in armor_only_checkboxes:
            def make_handler():
                def handler(event):
                    item_id = event.target.getAttribute("data-item-armor-only")
                    if item_id:
                        self.on_armor_only_toggle(event, item_id)
                return handler
            
            proxy = create_proxy(make_handler())
            checkbox.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
    
    # === Event Handler Methods (route to managers) ===
    
    def on_bonus_change(self, event, item_id: str):
        """
        Handle bonus value changes for armor/weapons.
        
        Flow: Extract value → Call manager setter → Manager updates data → Manager redraws UI
        """
        # Prevent event loops during programmatic updates
        if self._is_updating:
            console.log(f"[EVENT-LISTENER] Ignoring event during update: {item_id}")
            return
        
        console.log(f"[EVENT-LISTENER] on_bonus_change: item_id={item_id}")
        
        bonus_input = event.target
        bonus_val_str = bonus_input.value.strip()
        
        # Parse bonus value
        try:
            bonus_val = int(bonus_val_str) if bonus_val_str else 0
        except (ValueError, TypeError):
            bonus_val = 0
        
        # Get item to determine category
        item = self.inventory_manager.get_item(item_id)
        if not item:
            console.error(f"[EVENT-LISTENER] Item {item_id} not found")
            return
        
        category = item.get("category", "")
        console.log(f"[EVENT-LISTENER] Item category: {category}, bonus: {bonus_val}")
        
        # Route to appropriate manager
        if category == "Armor":
            # Armor/Shield: use armor_manager setter
            # Get armor_manager from sys.modules (where it was initialized by character.py)
            import sys
            armor_mgr = sys.modules.get('armor_manager')
            
            if not armor_mgr:
                console.error("[ARMOR-SET] armor_manager not in sys.modules, cannot set bonus")
                return
            
            console.log(f"[ARMOR-SET] Got armor_manager from sys.modules")
            
            # Set flag to prevent re-entrant event firing during update
            self._is_updating = True
            try:
                set_armor_bonus_func = getattr(armor_mgr, "set_armor_bonus")
                success = set_armor_bonus_func(self.inventory_manager, item_id, bonus_val)
                if success:
                    # Manager updates data, now redraw UI
                    self.inventory_manager.redraw_armor_items()
                    # Re-render the armor-grid table using module function
                    render_grid_func = getattr(armor_mgr, 'render_armor_grid', None)
                    if render_grid_func:
                        render_grid_func()
                        console.log("[EVENT-LISTENER] Re-rendered armor-grid table")
                    else:
                        console.warn("[EVENT-LISTENER] render_armor_grid not found in armor_manager")
                    # Update calculations (AC, etc.)
                    # The character module is already in sys.modules from initial load
                    try:
                        import sys
                        char_module = sys.modules.get('character')
                        if char_module:
                            update_func = getattr(char_module, 'update_calculations', None)
                            if update_func:
                                update_func()
                                console.log("[EVENT-LISTENER] Called update_calculations from sys.modules")
                            else:
                                console.warn("[EVENT-LISTENER] update_calculations not found in character module")
                            
                            # Trigger auto-export
                            trigger_export_func = getattr(char_module, 'trigger_auto_export', None)
                            if trigger_export_func:
                                trigger_export_func("armor_bonus_change")
                                console.log("[EVENT-LISTENER] Triggered auto-export")
                            else:
                                console.warn("[EVENT-LISTENER] trigger_auto_export not found in character module")
                        else:
                            console.warn("[EVENT-LISTENER] character module not in sys.modules")
                    except Exception as e2:
                        console.error(f"[EVENT-LISTENER] Error calling update_calculations: {e2}")
                else:
                    console.error("[EVENT-LISTENER] Failed to set armor bonus")
            except Exception as e:
                console.error(f"[ARMOR-SET] Error setting bonus: {e}")
                console.error(f"[EVENT-LISTENER] Failed to set armor bonus")
            finally:
                # Always clear flag, even if error occurs
                self._is_updating = False
        else:
            # For weapons/other items: handle bonus and update UI
            self._is_updating = True
            try:
                # Update the item bonus in inventory
                self.inventory_manager._handle_bonus_change(event, item_id)
                
                # Re-render inventory list
                self.inventory_manager.redraw_armor_items()
                
                # Re-render weapons grid if this is a weapon
                if category == "Weapons":
                    import sys
                    weapons_mgr_module = sys.modules.get('weapons_manager')
                    if weapons_mgr_module:
                        get_mgr_func = getattr(weapons_mgr_module, 'get_weapons_manager', None)
                        if get_mgr_func:
                            weapons_mgr = get_mgr_func()
                            if weapons_mgr:
                                weapons_mgr.render()
                                console.log("[EVENT-LISTENER] Re-rendered weapons-grid table")
                        else:
                            console.warn("[EVENT-LISTENER] get_weapons_manager not found")
                    else:
                        console.warn("[EVENT-LISTENER] weapons_manager not in sys.modules")
                
                # Update calculations and trigger export
                try:
                    import sys
                    char_module = sys.modules.get('character')
                    if char_module:
                        update_func = getattr(char_module, 'update_calculations', None)
                        if update_func:
                            update_func()
                            console.log("[EVENT-LISTENER] Called update_calculations from sys.modules")
                        
                        trigger_export_func = getattr(char_module, 'trigger_auto_export', None)
                        if trigger_export_func:
                            trigger_export_func("weapon_bonus_change")
                            console.log("[EVENT-LISTENER] Triggered auto-export")
                except Exception as e2:
                    console.error(f"[EVENT-LISTENER] Error calling update_calculations: {e2}")
            finally:
                self._is_updating = False
    
    def on_toggle_item(self, event, item_id: str):
        """Handle item expand/collapse toggle."""
        console.log(f"[EVENT-LISTENER] on_toggle_item: {item_id}")
        self.inventory_manager._handle_item_toggle(event, item_id)
    
    def on_remove_item(self, event, item_id: str):
        """Handle item removal."""
        console.log(f"[EVENT-LISTENER] on_remove_item: {item_id}")
        self.inventory_manager._handle_item_remove(event, item_id)
    
    def on_qty_change(self, event, item_id: str):
        """Handle quantity changes."""
        console.log(f"[EVENT-LISTENER] on_qty_change: {item_id}")
        self.inventory_manager._handle_qty_change(event, item_id)
    
    def on_category_change(self, event, item_id: str):
        """Handle category changes."""
        console.log(f"[EVENT-LISTENER] on_category_change: {item_id}")
        self.inventory_manager._handle_category_change(event, item_id)
    
    def on_equipped_toggle(self, event, item_id: str):
        """Handle equipped checkbox toggle."""
        console.log(f"[EVENT-LISTENER] on_equipped_toggle: {item_id}")
        self.inventory_manager._handle_equipped_toggle(event, item_id)
    
    def on_modifier_change(self, event, item_id: str, modifier_type: str):
        """Handle modifier changes (AC, saves, etc.)."""
        console.log(f"[EVENT-LISTENER] on_modifier_change: {item_id}, type={modifier_type}")
        self.inventory_manager._handle_modifier_change(event, item_id, modifier_type)
    
    def on_armor_only_toggle(self, event, item_id: str):
        """Handle armor-only checkbox toggle."""
        console.log(f"[EVENT-LISTENER] on_armor_only_toggle: {item_id}")
        self.inventory_manager._handle_armor_only_toggle(event, item_id)


# === Public API ===

_GLOBAL_EVENT_LISTENER: Optional[EquipmentEventListener] = None


def initialize_event_listener(inventory_manager):
    """
    Initialize the global event listener.
    
    Args:
        inventory_manager: The inventory manager instance
    
    Returns:
        The initialized event listener
    """
    global _GLOBAL_EVENT_LISTENER
    _GLOBAL_EVENT_LISTENER = EquipmentEventListener(inventory_manager)
    console.log("[EVENT-LISTENER] Global event listener initialized")
    return _GLOBAL_EVENT_LISTENER


def get_event_listener() -> Optional[EquipmentEventListener]:
    """Get the global event listener instance."""
    return _GLOBAL_EVENT_LISTENER


def register_all_events():
    """Register all event handlers (call after DOM updates)."""
    if _GLOBAL_EVENT_LISTENER:
        _GLOBAL_EVENT_LISTENER.register_all_handlers()
    else:
        console.error("[EVENT-LISTENER] Event listener not initialized")


# Alias functions for consistency
def initialize_equipment_event_manager(inventory_manager):
    """Alias for initialize_event_listener."""
    return initialize_event_listener(inventory_manager)


def get_equipment_event_manager():
    """Alias for get_event_listener."""
    return get_event_listener()