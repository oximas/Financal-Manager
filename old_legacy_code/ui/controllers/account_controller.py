"""Account controller"""
import customtkinter as ctk
from ui.controllers.base_controller import BaseViewController
from ui.components import MenuButton, MessageHelper
from config.settings import UIConfig


class AccountController(BaseViewController):
    """Controller for account settings screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Account Settings")
        
        # Username display
        username_label = ctk.CTkLabel(
            self.master,
            text=f"Username: {self.manager.current_username}",
            font=UIConfig.FONT_NORMAL
        )
        username_label.pack(pady=10)
        
        # Store buttons for navigation
        self.buttons = []
        self.current_button_index = 0
        
        # Action buttons
        button_configs = [
            ("Add Vault", self.on_add_vault, "secondary"),
            ("Change Password", self.on_change_password, "secondary"),
            ("Export data to Excel", self.on_export_excel, "secondary"),
            ("Logout", self.on_logout, "primary"),
            ("Back", self.on_back, "back")
        ]
        
        for text, command, btn_type in button_configs:
            btn = MenuButton(self.master, text, command, btn_type)
            btn.pack(pady=2)
            self.buttons.append(btn)
        
        # Highlight first button
        self._highlight_button(0)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for account screen."""
        # Arrow navigation for buttons
        self.master.bind('<Up>', lambda e: self._navigate_buttons(-1))
        self.master.bind('<Down>', lambda e: self._navigate_buttons(1))
        self.master.bind('<Return>', lambda e: self._activate_current_button())
        
        # Escape for back
        self.master.bind('<Escape>', lambda e: (self.on_back(), "break")[1])
    
    def _navigate_buttons(self, direction):
        """Navigate through buttons with arrow keys"""
        self._unhighlight_button(self.current_button_index)
        self.current_button_index = (self.current_button_index + direction) % len(self.buttons)
        self._highlight_button(self.current_button_index)
    
    def _highlight_button(self, index):
        """Highlight a button"""
        self.buttons[index].configure(
            fg_color=UIConfig.COLOR_SUCCESS,
            border_width=2,
            border_color=UIConfig.COLOR_TEXT_PRIMARY
        )
    
    def _unhighlight_button(self, index):
        """Remove highlight from button"""
        button = self.buttons[index]
        button.configure(
            fg_color=button.original_fg_color,
            border_width=0
        )
    
    def _activate_current_button(self):
        """Activate the currently selected button"""
        self.buttons[self.current_button_index].invoke()
    
    def on_add_vault(self):
        ask_dialog = ctk.CTkInputDialog(
            text="New vault name is:",
            title="Add new vault"
        )
        new_vault_name = ask_dialog.get_input()
        
        if new_vault_name:
            try:
                self.manager.add_vault_to_current_user(new_vault_name)
                MessageHelper.show_info(
                    "Success",
                    f"Vault '{new_vault_name}' added successfully!"
                )
            except:
                MessageHelper.show_error(
                    "Failed to add new vault",
                    f"Vault '{new_vault_name}' already exists in your vaults!"
                )
        elif new_vault_name == "":
            MessageHelper.show_error("Error", "Vault name can't be empty")
    
    def on_change_password(self):
        # Placeholder for future implementation
        MessageHelper.show_info("Not Implemented", "Password change feature coming soon!")
    
    def on_export_excel(self):
        try:
            # if didnt work use tkinter instead not ctk
            file_path = ctk.filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if file_path:
                self.manager.export_current_user_db_to_excel(file_path)
                MessageHelper.show_info("Success", f"Data exported successfully to {file_path}!")
            else:
                MessageHelper.show_info("Export Failed", "You didn't choose a path")
        except PermissionError:
            MessageHelper.show_error(
                "Export Failed",
                "Please close any instances of the file and make sure you have write permissions"
            )
        except Exception as e:
            MessageHelper.show_error("Export Failed", str(e))
    
    def on_logout(self):
        self.manager.logout()
        from ui.controllers.main_menu_controller import MainMenuController
        self.transition_to(MainMenuController)
    
    def on_back(self):
        from ui.controllers.user_menu_controller import UserMenuController
        self.transition_to(UserMenuController)

    def cleanup(self):
        """Cleanup arrow key bindings"""
        navigation_keys = ['<Up>', '<Down>', '<Return>', '<Escape>']
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass
        super().cleanup()
