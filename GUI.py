# gui.py
"""Main GUI application class"""
import customtkinter as ctk
from customtkinter import set_appearance_mode, set_default_color_theme
from config import UIConfig, AppConfig
from manager import Manager
from Database import Database
from view_factory import ViewFactory


class FinanceManagerGUI:
    """
    Main GUI application for the Finance Manager.
    
    This class follows the Single Responsibility Principle by delegating
    view management to ViewFactory and business logic to Manager.
    """
    
    def __init__(self):
        self._initialize_settings()
        self._initialize_backend()
        self._initialize_window()
    
    def _initialize_settings(self):
        """Initialize CustomTkinter settings"""
        set_appearance_mode(AppConfig.APPEARANCE_MODE)
        set_default_color_theme(AppConfig.COLOR_THEME)
    
    def _initialize_backend(self):
        """Initialize database and manager"""
        self.database = Database(AppConfig.DB_NAME)
        self.manager = Manager(AppConfig.DB_NAME)
    
    def _initialize_window(self):
        """Initialize the main window"""
        self.master = ctk.CTk()
        self.master.title("Finance Manager")
        self.master.geometry(
            f"{UIConfig.DEFAULT_WIDTH}x{UIConfig.DEFAULT_HEIGHT}"
        )
        self.master.configure(fg_color=UIConfig.COLOR_BACKGROUND)
    
    def run(self):
        """Start the application"""
        # Show the main menu
        ViewFactory.show_main_menu(self.master, self.manager, self.database)
        
        # For debugging specific menus, uncomment and modify:
        # self.manager._current_username = "TestUser"
        # ViewFactory.show_user_menu(self.master, self.manager, self.database)
        
        # Start the main event loop
        self.master.mainloop()
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'database'):
            self.database.close()
