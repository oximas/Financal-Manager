# utils/focus_manager.py
"""
Focus-aware keyboard navigation system.
Manages intelligent key routing based on widget type and navigation mode.
"""
from enum import Enum
from typing import Callable, Optional, List, Any
import customtkinter as ctk
from tkinter import Entry, Text


class NavigationMode(Enum):
    """Navigation modes for different screen types"""
    MENU = "menu"      # Arrow keys navigate buttons, Enter activates
    FORM = "form"      # Smart navigation, Enter submits
    GRID = "grid"      # Excel-like cell navigation


class WidgetType(Enum):
    """Widget types for focus-aware handling"""
    TEXT_INPUT = "text_input"      # Entry fields
    DROPDOWN = "dropdown"          # ComboBox
    BUTTON = "button"              # Buttons
    DATE_PICKER = "date_picker"    # Date picker entry
    UNKNOWN = "unknown"


class FocusManager:
    """
    Manages focus-aware keyboard navigation.
    Routes keys intelligently based on focused widget and navigation mode.
    """
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize focus manager.
        
        Args:
            root: The root tkinter window
        """
        self.root = root
        self.mode = NavigationMode.FORM
        self._bound_keys: List[str] = []
        
        # Callbacks
        self.on_submit: Optional[Callable] = None
        self.on_back: Optional[Callable] = None
        
        # Navigation state
        self.navigable_widgets: List[Any] = []
        self.current_focus_index: int = 0
    
    def enable_navigation(
        self,
        mode: NavigationMode,
        on_submit: Optional[Callable] = None,
        on_back: Optional[Callable] = None,
        navigable_widgets: Optional[List[Any]] = None
    ) -> None:
        """
        Enable smart navigation for this mode.
        
        Args:
            mode: Navigation mode (MENU, FORM, GRID)
            on_submit: Callback for submit action (Enter key)
            on_back: Callback for back action (Escape key)
            navigable_widgets: List of widgets to navigate (for MENU mode)
        """
        self.mode = mode
        self.on_submit = on_submit
        self.on_back = on_back
        self.navigable_widgets = navigable_widgets or []
        
        # Clear previous bindings
        self.disable_navigation()
        
        # Bind keys based on mode
        if mode == NavigationMode.MENU:
            self._enable_menu_navigation()
        elif mode == NavigationMode.FORM:
            self._enable_form_navigation()
        elif mode == NavigationMode.GRID:
            self._enable_grid_navigation()
        
        # Always bind Escape for back
        if on_back:
            self._bind_key('<Escape>', lambda e: self._handle_escape())
    
    def disable_navigation(self) -> None:
        """Disable all navigation bindings"""
        for key in self._bound_keys:
            try:
                self.root.unbind(key)
            except:
                pass
        self._bound_keys.clear()
    
    # ==================== MODE-SPECIFIC NAVIGATION ====================
    
    def _enable_menu_navigation(self) -> None:
        """Enable navigation for menu mode (button navigation)"""
        self._bind_key('<Up>', lambda e: self._navigate_menu(-1))
        self._bind_key('<Down>', lambda e: self._navigate_menu(1))
        self._bind_key('<Return>', lambda e: self._activate_menu_button())
    
    def _enable_form_navigation(self) -> None:
        """Enable navigation for form mode (smart field navigation)"""
        self._bind_key('<Up>', lambda e: self._handle_arrow_in_form('up'))
        self._bind_key('<Down>', lambda e: self._handle_arrow_in_form('down'))
        self._bind_key('<Return>', lambda e: self._handle_enter_in_form())
    
    def _enable_grid_navigation(self) -> None:
        """Enable navigation for grid mode (Excel-like)"""
        self._bind_key('<Up>', lambda e: self._handle_arrow_in_grid('up'))
        self._bind_key('<Down>', lambda e: self._handle_arrow_in_grid('down'))
        self._bind_key('<Left>', lambda e: self._handle_arrow_in_grid('left'))
        self._bind_key('<Right>', lambda e: self._handle_arrow_in_grid('right'))
        self._bind_key('<Return>', lambda e: self._handle_enter_in_grid())
    
    # ==================== MENU MODE HANDLERS ====================
    
    def _navigate_menu(self, direction: int) -> str:
        """Navigate between menu buttons"""
        if not self.navigable_widgets:
            return "break"
        
        # This is handled by the controller's own navigation
        # We just prevent default behavior
        return "break"
    
    def _activate_menu_button(self) -> str:
        """Activate currently selected menu button"""
        # This is handled by the controller
        return "break"
    
    # ==================== FORM MODE HANDLERS ====================
    
    def _handle_arrow_in_form(self, direction: str) -> str:
        """
        Handle arrow keys in form mode.
        
        Strategy:
        - If focused on text input: check cursor position
          - If at start and Up/Left: navigate to previous field
          - If at end and Down/Right: navigate to next field
          - Otherwise: let widget handle it (move cursor)
        - If focused on dropdown: let widget handle it (navigate options)
        - If focused on button: navigate to prev/next widget
        """
        focused = self.root.focus_get()
        
        if not focused:
            return "break"
        
        widget_type = self._get_widget_type(focused)
        
        # TEXT INPUT: Smart navigation
        if widget_type == WidgetType.TEXT_INPUT:
            should_navigate = self._should_navigate_from_text_input(
                focused, direction
            )
            
            if should_navigate:
                if direction in ['up', 'left']:
                    focused.tk_focusPrev().focus_set()
                else:  # down, right
                    focused.tk_focusNext().focus_set()
                return "break"
            else:
                # Let widget handle cursor movement
                return None  # Don't break, allow default
        
        # DROPDOWN: Always let widget handle
        elif widget_type == WidgetType.DROPDOWN:
            return None  # Allow default dropdown navigation
        
        # BUTTON: Navigate to prev/next field
        elif widget_type == WidgetType.BUTTON:
            if direction in ['up', 'left']:
                focused.tk_focusPrev().focus_set()
            else:
                focused.tk_focusNext().focus_set()
            return "break"
        
        return "break"
    
    def _handle_enter_in_form(self) -> str:
        """
        Handle Enter key in form mode.
        
        Strategy:
        - If focused on text input: submit form
        - If focused on dropdown: open dropdown menu
        - If focused on button: activate button
        """
        focused = self.root.focus_get()
        
        if not focused:
            if self.on_submit:
                self.on_submit()
            return "break"
        
        widget_type = self._get_widget_type(focused)
        
        # TEXT INPUT or DATE_PICKER: Submit form
        if widget_type in [WidgetType.TEXT_INPUT, WidgetType.DATE_PICKER]:
            if self.on_submit:
                self.on_submit()
            return "break"
        
        # DROPDOWN: Open dropdown (let widget handle)
        elif widget_type == WidgetType.DROPDOWN:
            # Simulate click to open dropdown
            try:
                focused.event_generate('<Button-1>')
            except:
                pass
            return "break"
        
        # BUTTON: Activate button
        elif widget_type == WidgetType.BUTTON:
            try:
                focused.invoke()
            except:
                pass
            return "break"
        
        # DEFAULT: Submit
        if self.on_submit:
            self.on_submit()
        return "break"
    
    # ==================== GRID MODE HANDLERS ====================
    
    def _handle_arrow_in_grid(self, direction: str) -> str:
        """
        Handle arrow keys in grid mode (Excel-like navigation).
        
        For now, we'll let the grid handle this internally.
        This is a placeholder for future grid navigation logic.
        """
        # Grid navigation is handled by BulkTransactionGrid
        # We just prevent interference
        return None  # Allow default behavior
    
    def _handle_enter_in_grid(self) -> str:
        """
        Handle Enter in grid mode.
        
        Strategy:
        - If in dropdown: open dropdown
        - Otherwise: submit form
        """
        focused = self.root.focus_get()
        
        if focused:
            widget_type = self._get_widget_type(focused)
            
            # DROPDOWN: Open it
            if widget_type == WidgetType.DROPDOWN:
                try:
                    focused.event_generate('<Button-1>')
                except:
                    pass
                return "break"
        
        # Otherwise submit
        if self.on_submit:
            self.on_submit()
        return "break"
    
    # ==================== HELPER METHODS ====================
    
    def _handle_escape(self) -> str:
        """Handle Escape key (back/cancel)"""
        if self.on_back:
            self.on_back()
        return "break"
    
    def _get_widget_type(self, widget: Any) -> WidgetType:
        """
        Determine widget type from widget instance.
        
        Args:
            widget: The widget to check
            
        Returns:
            WidgetType enum value
        """
        # Check for CTk widgets
        if isinstance(widget, ctk.CTkEntry):
            return WidgetType.TEXT_INPUT
        elif isinstance(widget, ctk.CTkComboBox):
            return WidgetType.DROPDOWN
        elif isinstance(widget, ctk.CTkButton):
            return WidgetType.BUTTON
        
        # Check for standard tkinter widgets (inside CTk widgets)
        elif isinstance(widget, Entry):
            return WidgetType.TEXT_INPUT
        elif isinstance(widget, Text):
            return WidgetType.TEXT_INPUT
        
        # Check widget class name as fallback
        class_name = widget.winfo_class()
        if 'Entry' in class_name:
            return WidgetType.TEXT_INPUT
        elif 'Combobox' in class_name or 'OptionMenu' in class_name:
            return WidgetType.DROPDOWN
        elif 'Button' in class_name:
            return WidgetType.BUTTON
        
        return WidgetType.UNKNOWN
    
    def _should_navigate_from_text_input(
        self,
        entry_widget: Any,
        direction: str
    ) -> bool:
        """
        Determine if we should navigate away from text input.
        
        Returns True if:
        - Direction is UP/LEFT and cursor is at position 0
        - Direction is DOWN/RIGHT and cursor is at end
        
        Args:
            entry_widget: The entry widget
            direction: 'up', 'down', 'left', 'right'
            
        Returns:
            True if should navigate to prev/next field
        """
        try:
            # Get the underlying tk Entry widget
            if hasattr(entry_widget, '_entry'):
                tk_entry = entry_widget._entry
            else:
                tk_entry = entry_widget
            
            # Get cursor position
            cursor_pos = tk_entry.index('insert')
            text_length = len(tk_entry.get())
            
            # Check if at boundaries
            if direction in ['up', 'left']:
                return cursor_pos == 0
            elif direction in ['down', 'right']:
                return cursor_pos == text_length
            
        except Exception:
            # If we can't determine, don't navigate
            return False
        
        return False
    
    def _bind_key(self, key_sequence: str, callback: Callable) -> None:
        """
        Bind a key and track it for cleanup.
        
        Args:
            key_sequence: Key sequence to bind
            callback: Callback function
        """
        self.root.bind(key_sequence, callback)
        self._bound_keys.append(key_sequence)
    
    def set_navigable_widgets(self, widgets: List[Any]) -> None:
        """
        Set the list of navigable widgets (for MENU mode).
        
        Args:
            widgets: List of widgets to navigate
        """
        self.navigable_widgets = widgets
        self.current_focus_index = 0