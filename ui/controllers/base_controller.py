"""Base controller for all view controllers"""
import customtkinter as ctk
from core.manager import Manager
from config.settings import UIConfig
from utils.key_bindings import KeyBindingManager
from utils.focus_manager import FocusManager, NavigationMode


class BaseViewController:
    """
    Base class for all view controllers.
    Handles widget management and keyboard shortcuts.
    """
    
    def __init__(self, master: ctk.CTk, manager: Manager):
        """
        Initialize the base view controller.
        
        Args:
            master: The root tkinter window
            manager: The business logic manager
        """
        self.master = master
        self.manager = manager
        self.widgets = []
        
        # Initialize key binding manager
        self.key_manager = KeyBindingManager(master)
        self.focus_manager = FocusManager(master)

        # CRITICAL: Unbind ALL previous bindings when creating new controller
        self._unbind_all_navigation_keys()
    
    def _unbind_all_navigation_keys(self):
        """Unbind all navigation keys from previous controllers"""
        navigation_keys = [
            '<Up>', '<Down>', '<Left>', '<Right>',
            '<Return>', '<Tab>', '<Shift-Tab>'
        ]
        
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass

    def clear_widgets(self) -> None:
        """Remove all widgets from the screen."""
        for widget in self.master.winfo_children():
            widget.destroy()
        self.widgets.clear()
    
    def setup_key_bindings(self) -> None:
        """
        Setup keyboard shortcuts for this view.
        Override this method in child classes to define view-specific bindings.
        
        Example:
            def setup_key_bindings(self):
                self.key_manager.bind_multiple([
                    (KeyAction.SUBMIT, self.on_submit),
                    (KeyAction.BACK, self.on_back)
                ])
        """
        pass
    
    def cleanup(self) -> None:
        """
        Cleanup resources when leaving this view.
        Automatically unbinds all key bindings.
        Override to add additional cleanup logic.
        """
        self.key_manager.unbind_all()
        self.focus_manager.disable_navigation()
        
    def _resize_window_small(self):
        """Resize window to fit content"""
        self.master.update_idletasks()
        width = self.master.winfo_reqwidth()
        height = self.master.winfo_reqheight()
        margin = UIConfig.WINDOW_MARGIN

        new_width = max(width + margin, UIConfig.DEFAULT_WIDTH)
        new_height = max(height + margin, UIConfig.DEFAULT_HEIGHT)
        
        self.master.geometry(f"{new_width}x{new_height}")
    
    def _resize_window_maximize(self):
        """Maximize window"""
        self.master.update_idletasks()
        self.master.state('zoomed')

    def _resize_window_fullscreen(self):
        """Fullscreen window"""
        self.master.update_idletasks()
        self.master.attributes("-fullscreen", True)

    def is_maximized(self) -> bool:
        return self.master.state() == "zoomed"
    
    def is_fullscreen(self) -> bool:
        return self.master.attributes('-fullscreen')
    
    def _resize_window(self):
        """resize window to fit the previous screen size"""
        if self.is_fullscreen():
            self._resize_window_fullscreen()
        elif self.is_maximized():
            self._resize_window_maximize()
        else:
            self._resize_window_small()
            
    def _resize_window_initial(self):
        self._resize_window_small()

    def show(self) -> None:
        """
        Display this view.
        Must be overridden by child classes.
        """
        raise NotImplementedError("Subclasses must implement show()")
    
    def transition_to(self, view_controller) -> None:
        """
        Helper method to transition to another view with proper cleanup.
        
        Args:
            view_controller: The view controller class to transition to
        
        Example:
            self.transition_to(LoginController)
        """
        self.cleanup()
        next_window = view_controller(self.master, self.manager)
        next_window.show()
        next_window._resize_window()
