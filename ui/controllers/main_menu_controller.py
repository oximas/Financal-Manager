"""Main menu controller"""
from ui.controllers.base_controller import BaseViewController
from ui.components import MenuButton
from config.settings import UIConfig


class MainMenuController(BaseViewController):
    """Controller for the main welcome screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Finance Manager - Welcome")
        
        # Store buttons for navigation
        self.buttons = []
        self.current_button_index = 0
        
        login_btn = MenuButton(
            self.master,
            "Login",
            self.on_login_clicked
        )
        login_btn.pack(pady=10)
        self.buttons.append(login_btn)
        
        signup_btn = MenuButton(
            self.master,
            "Sign Up",
            self.on_signup_clicked
        )
        signup_btn.pack(pady=10)
        self.buttons.append(signup_btn)
        
        # Highlight first button
        self._highlight_button(0)
        
        # Setup navigation
        self.setup_key_bindings()
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts for main menu"""
        self.master.bind('<Up>', lambda e: self._navigate_buttons(-1))
        self.master.bind('<Down>', lambda e: self._navigate_buttons(1))
        self.master.bind('<Return>', lambda e: self._activate_current_button())
        self.master.bind('<Escape>', lambda e: "break")
    
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
    
    def on_login_clicked(self):
        from ui.controllers.login_controller import LoginController
        self.transition_to(LoginController)
    
    def on_signup_clicked(self):
        from ui.controllers.signup_controller import SignupController
        self.transition_to(SignupController)

    def cleanup(self):
        """Cleanup arrow key bindings"""
        navigation_keys = ['<Up>', '<Down>', '<Return>', '<Escape>']
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass
        super().cleanup()
