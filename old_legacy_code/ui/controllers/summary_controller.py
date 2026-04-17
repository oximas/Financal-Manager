"""Summary controller"""
import customtkinter as ctk
from ui.controllers.base_controller import BaseViewController
from ui.components import MenuButton, VaultSummaryCard
from config.settings import UIConfig


class SummaryController(BaseViewController):
    """Controller for summary screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Summary Menu")
        
        # Main container frame
        container = ctk.CTkFrame(
            self.master,
            corner_radius=15,
            fg_color=UIConfig.COLOR_FRAME_LIGHT
        )
        container.pack(pady=20, padx=30, fill='both', expand=True)
        
        # Total Balance Label
        total_balance = self.manager.get_total_balance()
        total_label = ctk.CTkLabel(
            container,
            text=f"Total Amount: {total_balance:.2f} EGP",
            font=UIConfig.FONT_HEADING,
            text_color=UIConfig.COLOR_SUCCESS
        )
        total_label.pack(pady=15)
        
        # Vault Details Section
        vault_frame = ctk.CTkFrame(
            container,
            corner_radius=10,
            fg_color=UIConfig.COLOR_FRAME_DARK
        )
        vault_frame.pack(pady=10, padx=10, fill='x')
        
        vault_title = ctk.CTkLabel(
            vault_frame,
            text="Vault Details:",
            font=UIConfig.FONT_SUBHEADING,
            text_color=UIConfig.COLOR_TEXT_PRIMARY
        )
        vault_title.pack(pady=5)
        
        vaults = self.manager.get_current_user_vaults()
        for vault_name, balance in vaults.items():
            vault_card = VaultSummaryCard(vault_frame, vault_name, balance)
            vault_card.pack(pady=3, padx=10, fill='x')
        
        # Back Button
        back_button = MenuButton(
            container,
            "Back",
            self.on_back,
            button_type="primary"
        )
        back_button.pack(pady=20)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for summary screen."""
        self.master.bind('<Escape>', lambda e: (self.on_back(), "break")[1])
        
    def on_back(self):
        from ui.controllers.user_menu_controller import UserMenuController
        self.transition_to(UserMenuController)
