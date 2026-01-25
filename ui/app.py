# ui/app.py
"""Main GUI application class"""
import customtkinter as ctk
from customtkinter import set_appearance_mode, set_default_color_theme
from config.settings import UIConfig, AppConfig
from core.manager import Manager
from ui.controllers import BaseViewController, MainMenuController


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
        self._setup_global_shortcuts()
    
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
    
    def _setup_global_shortcuts(self):
        """
        Setup application-wide keyboard shortcuts.
        All global shortcuts use Ctrl+Shift to avoid conflicts with standard actions.
        """
        # Ctrl+Shift+F1-F5: Quick jump to menus
        self.master.bind('<Control-Shift-F1>', lambda e: self._quick_menu_jump('deposit'))
        self.master.bind('<Control-Shift-F2>', lambda e: self._quick_menu_jump('withdraw'))
        self.master.bind('<Control-Shift-F3>', lambda e: self._quick_menu_jump('transfer'))
        self.master.bind('<Control-Shift-F4>', lambda e: self._quick_menu_jump('summary'))
        self.master.bind('<Control-Shift-F5>', lambda e: self._quick_menu_jump('account'))
        
        # Ctrl+Shift+E: Export to Excel
        self.master.bind('<Control-Shift-E>', lambda e: self._quick_export())
        self.master.bind('<Control-Shift-e>', lambda e: self._quick_export())
        
        # Ctrl+Shift+V: Add new vault
        self.master.bind('<Control-Shift-V>', lambda e: self._quick_add_vault())
        self.master.bind('<Control-Shift-v>', lambda e: self._quick_add_vault())
    
    def _quick_menu_jump(self, menu_name: str):
        """
        Quick jump to a menu using keyboard shortcut.
        Only works when logged in.
        """
        if not self.manager.is_logged_in:
            return
        
        # Import here to avoid circular imports
        from ui.controllers import (
            DepositController, WithdrawController, TransferController,
            SummaryController, AccountController
        )
        
        menu_map = {
            'deposit': DepositController,
            'withdraw': WithdrawController,
            'transfer': TransferController,
            'summary': SummaryController,
            'account': AccountController
        }
        
        if menu_name in menu_map:
            controller_class = menu_map[menu_name]
            controller = controller_class(self.master, self.manager)
            controller.show()
    
    def _quick_export(self):
        """
        Quick export to Excel.
        Centralized export logic (not tied to AccountController).
        """
        if not self.manager.is_logged_in:
            return
        
        from ui.components import MessageHelper
        
        try:
            file_path = ctk.filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if file_path:
                self.manager.export_current_user_db_to_excel(file_path)
                MessageHelper.show_info(
                    "Success",
                    f"Data exported successfully to {file_path}!"
                )
            else:
                MessageHelper.show_info("Export Cancelled", "No file path selected")
        except PermissionError:
            MessageHelper.show_error(
                "Export Failed",
                "Please close the file if it's open and ensure you have write permissions"
            )
        except Exception as e:
            MessageHelper.show_error("Export Failed", str(e))
    
    def _quick_add_vault(self):
        """
        Quick add vault dialog.
        Centralized vault creation (not tied to AccountController).
        """
        if not self.manager.is_logged_in:
            return
        
        from ui.components import MessageHelper
        
        dialog = ctk.CTkInputDialog(
            text="New vault name:",
            title="Add Vault"
        )
        vault_name = dialog.get_input()
        
        if vault_name:
            try:
                self.manager.add_vault_to_current_user(vault_name)
                MessageHelper.show_info(
                    "Success",
                    f"Vault '{vault_name}' added successfully!"
                )
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
        BaseViewController(self.master, self.manager).transition_to(MainMenuController)
        
        # Start the main event loop
        self.master.mainloop()