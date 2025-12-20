# key_binding_manager.py
"""
Key binding management for the Finance Manager application.
Handles keyboard shortcuts with automatic cleanup and centralized configuration.
"""
from typing import Callable, Dict, Optional, List
import customtkinter as ctk
from enum import Enum


class KeyAction(Enum):
    """Standard key actions used across the application"""
    SUBMIT = "submit"
    BACK = "back"
    CANCEL = "cancel"
    REFRESH = "refresh"
    HELP = "help"


class KeyBinding:
    """Represents a single key binding configuration"""
    
    def __init__(
        self,
        key_sequence: str,
        action: KeyAction,
        callback: Callable,
        description: str = ""
    ):
        """
        Initialize a key binding.
        
        Args:
            key_sequence: The key sequence (e.g., '<Return>', '<Control-BackSpace>')
            action: The action this binding performs
            callback: The function to call when key is pressed
            description: Human-readable description of the binding
        """
        self.key_sequence = key_sequence
        self.action = action
        self.callback = callback
        self.description = description
    
    def __repr__(self) -> str:
        return f"KeyBinding({self.key_sequence} -> {self.action.value})"


class KeyBindingManager:
    """
    Manages keyboard shortcuts for the application.
    Handles binding, unbinding, and cleanup of key events.
    """
    
    # Default key mappings - can be customized or loaded from config
    DEFAULT_BINDINGS = {
        KeyAction.SUBMIT: '<Return>',
        KeyAction.BACK: '<Control-BackSpace>',
        KeyAction.CANCEL: '<Escape>',
        KeyAction.REFRESH: '<F5>',
        KeyAction.HELP: '<F1>'
    }
    
    def __init__(self, widget: ctk.CTk):
        """
        Initialize the key binding manager.
        
        Args:
            widget: The root widget to bind keys to (usually the main window, mostly called "root" or "master")
        """
        self.widget = widget
        self.active_bindings: Dict[str, KeyBinding] = {}
        self._binding_ids: Dict[str, str] = {}  # Track tkinter binding IDs
    
    def bind(
        self,
        action: KeyAction,
        callback: Callable,
        key_sequence: Optional[str] = None,
        description: str = ""
    ) -> None:
        """
        Bind a key action to a callback.
        
        Args:
            action: The action to bind
            callback: The function to call when key is pressed
            key_sequence: Optional custom key sequence (uses default if None)
            description: Human-readable description
        """
        # Use provided key sequence or fall back to default
        key_seq = key_sequence or self.DEFAULT_BINDINGS.get(action)
        
        if not key_seq:
            raise ValueError(f"No key sequence defined for action {action}")
        
        # Create the binding
        binding = KeyBinding(key_seq, action, callback, description)
        
        # Unbind if this action was already bound
        if action.value in self.active_bindings:
            self.unbind(action)
        
        # Create wrapper to handle event parameter
        def event_wrapper(event):
            callback()
            return "break"  # Prevent event propagation
        
        # Bind to the widget and store the binding ID
        binding_id = self.widget.bind(key_seq, event_wrapper)
        
        # Track the binding
        self.active_bindings[action.value] = binding
        self._binding_ids[action.value] = binding_id
    
    def bind_multiple(self, bindings: List[tuple]) -> None:
        """
        Bind multiple key actions at once.
        
        Args:
            bindings: List of tuples (action, callback) or (action, callback, key_sequence)
        
        Example:
            manager.bind_multiple([
                (KeyAction.SUBMIT, self.on_submit),
                (KeyAction.BACK, self.on_back),
                (KeyAction.CANCEL, self.on_cancel, '<Control-c>')
            ])
        """
        for binding in bindings:
            if len(binding) == 2:
                action, callback = binding
                self.bind(action, callback)
            elif len(binding) == 3:
                action, callback, key_seq = binding
                self.bind(action, callback, key_seq)
            else:
                raise ValueError(f"Invalid binding tuple: {binding}")
    
    def unbind(self, action: KeyAction) -> None:
        """
        Unbind a specific key action.
        
        Args:
            action: The action to unbind
        """
        action_key = action.value
        
        if action_key not in self.active_bindings:
            return
        
        binding = self.active_bindings[action_key]
        
        # Unbind from the widget
        self.widget.unbind(binding.key_sequence)
        
        # Remove from tracking
        del self.active_bindings[action_key]
        if action_key in self._binding_ids:
            del self._binding_ids[action_key]
    
    def unbind_all(self) -> None:
        """Unbind all active key bindings."""
        # Create a copy of keys to avoid dictionary size change during iteration
        actions = list(self.active_bindings.keys())
        
        for action_key in actions:
            action = KeyAction(action_key)
            self.unbind(action)
    
    def get_active_bindings(self) -> Dict[KeyAction, str]:
        """
        Get all currently active key bindings.
        
        Returns:
            Dictionary mapping actions to their key sequences
        """
        return {
            KeyAction(key): binding.key_sequence
            for key, binding in self.active_bindings.items()
        }
    
    def get_binding_info(self, action: KeyAction) -> Optional[KeyBinding]:
        """
        Get information about a specific binding.
        
        Args:
            action: The action to query
            
        Returns:
            KeyBinding object or None if not bound
        """
        return self.active_bindings.get(action.value)
    
    def is_bound(self, action: KeyAction) -> bool:
        """
        Check if an action is currently bound.
        
        Args:
            action: The action to check
            
        Returns:
            True if the action is bound, False otherwise
        """
        return action.value in self.active_bindings
    
    def print_bindings(self) -> None:
        """Print all active bindings (useful for debugging)."""
        print("\n=== Active Key Bindings ===")
        for action_key, binding in self.active_bindings.items():
            desc = f" - {binding.description}" if binding.description else ""
            print(f"{binding.key_sequence}: {action_key}{desc}")
        print("===========================\n")


# Optional: Configuration class for customizable shortcuts
class KeyBindingConfig:
    """
    Configuration for customizable key bindings.
    Can be extended to load from a config file or user preferences.
    """
    
    @staticmethod
    def get_default_config() -> Dict[KeyAction, str]:
        """Get the default key binding configuration."""
        return KeyBindingManager.DEFAULT_BINDINGS.copy()
    
    @staticmethod
    def load_from_file(filepath: str) -> Dict[KeyAction, str]:
        """
        Load key bindings from a configuration file.
        
        Args:
            filepath: Path to the configuration file
            
        Returns:
            Dictionary of key bindings
            
        Note:
            This is a placeholder for future implementation.
        """
        # TODO: Implement config file loading (JSON, YAML, etc.)
        raise NotImplementedError("Config file loading not yet implemented")
    
    @staticmethod
    def save_to_file(filepath: str, bindings: Dict[KeyAction, str]) -> None:
        """
        Save key bindings to a configuration file.
        
        Args:
            filepath: Path to save the configuration
            bindings: Dictionary of key bindings to save
            
        Note:
            This is a placeholder for future implementation.
        """
        # TODO: Implement config file saving
        raise NotImplementedError("Config file saving not yet implemented")