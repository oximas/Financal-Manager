"""Signup controller"""
from ui.controllers.base_controller import BaseViewController
from ui.components import CenteredForm, FormBuilder, MessageHelper
from config.settings import UIConfig
from core.result_types import AuthSuccess
from utils.focus_manager import NavigationMode


class SignupController(BaseViewController):
    """Controller for the signup screen"""
    
    def show(self):
        """Display the signup view."""
        self.clear_widgets()
        self.master.title("Sign Up")
        
        # Create the GUI
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Sign Up") \
            .add_field("username", "Username:", placeholder="Enter username") \
            .add_field("password", "Password:", placeholder="Enter password", show="*") \
            .add_field("confirm_password", "Confirm Password:", placeholder="Confirm password", show="*") \
            .add_button("Sign Up", self.on_submit, UIConfig.COLOR_PRIMARY, UIConfig.COLOR_TEXT_DARK) \
            .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for signup screen."""
        self.focus_manager.enable_navigation(
            mode=NavigationMode.FORM,
            on_submit=self.on_submit,
            on_back=self.on_back
        )
    
    def on_submit(self):
        """Handle signup submission."""
        values = self.form.get_values()
        result = self.manager.signup(
            values["username"],
            values["password"],
            values["confirm_password"]
        )
        
        if isinstance(result, AuthSuccess):
            from ui.controllers.user_menu_controller import UserMenuController
            self.transition_to(UserMenuController)
        else:
            MessageHelper.show_error("Signup Failed", result.message)
    
    def on_back(self):
        """Navigate back to main menu."""
        from ui.controllers.main_menu_controller import MainMenuController
        self.transition_to(MainMenuController)
