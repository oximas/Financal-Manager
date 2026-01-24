# ui/app.py
"""Main GUI application class"""
import customtkinter as ctk
from customtkinter import set_appearance_mode, set_default_color_theme
from config.settings import UIConfig, AppConfig
from core.manager import Manager
from ui.controllers import AccountController, BaseViewController, MainMenuController, SummaryController, TransferController, WithdrawController, DepositController


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
        """Initialize manager"""
        self.manager = Manager(AppConfig.DB_PATH)
    
    def _initialize_window(self):
        """Initialize the main window"""
        self.master = ctk.CTk()
        self.master.title("Finance Manager")
        self.master.geometry(
            f"{UIConfig.DEFAULT_WIDTH}x{UIConfig.DEFAULT_HEIGHT}"
        )
        self.master.configure(fg_color=UIConfig.COLOR_BACKGROUND)
        
        # Setup global key bindings
        self._setup_global_shortcuts()
    
    def _setup_global_shortcuts(self):
        """Setup application-wide keyboard shortcuts"""
        # Ctrl+F1-F5: Jump to menus (only when logged in)
        self.master.bind('<Control-F1>', lambda e: self._quick_menu_jump('deposit'))
        self.master.bind('<Control-F2>', lambda e: self._quick_menu_jump('withdraw'))
        self.master.bind('<Control-F3>', lambda e: self._quick_menu_jump('transfer'))
        self.master.bind('<Control-F4>', lambda e: self._quick_menu_jump('summary'))
        self.master.bind('<Control-F5>', lambda e: self._quick_menu_jump('account'))
        
        # Ctrl+E: Export to Excel
        self.master.bind('<Control-e>', lambda e: self._quick_export())
        
        # Ctrl+V: Add new vault
        self.master.bind('<Control-v>', lambda e: self._quick_add_vault())
    
    def _quick_menu_jump(self, menu_name: str):
        """Jump to a menu using keyboard shortcut"""
        if not self.manager.is_logged_in:
            return  # Do nothing if not logged in (silent)
        
        menu_map = {
            'deposit': DepositController,
            'withdraw': WithdrawController,
            'transfer': TransferController,
            'summary': SummaryController,
            'account': AccountController
        }
        
        if menu_name in menu_map:
            menu_map[menu_name]()
    
    def _quick_export(self):
        """Quick export to Excel"""
        if not self.manager.is_logged_in:
            return  # Do nothing if not logged in (silent)
        
        AccountController(self.master,self.manager).on_export_excel()
    
    def _quick_add_vault(self):
        """Quick add vault dialog"""
        if not self.manager.is_logged_in:
            return  # Do nothing if not logged in (silent)
        
        from ui.components import MessageHelper
        
        dialog = ctk.CTkInputDialog(
            text="New vault name:",
            title="Add Vault"
        )
        vault_name = dialog.get_input()
        
        if vault_name:
            try:
                self.manager.add_vault_to_current_user(vault_name)
                MessageHelper.show_info("Success", f"Vault '{vault_name}' added successfully!")
            except:
                MessageHelper.show_error(
                    "Error",
                    f"Vault '{vault_name}' already exists in your vaults!"
                )
        elif vault_name == "":
            MessageHelper.show_error("Error", "Vault name can't be empty")
    
    def run(self):
        """Start the application"""
        # Show the main menu
        BaseViewController(self.master,self.manager).transition_to(MainMenuController)
        # For debugging specific menus, uncomment and modify:
        # self.manager._current_username = "TestUser"
        # ViewFactory.show_user_menu(self.master, self.manager)
        
        # Start the main event loop
        self.master.mainloop()