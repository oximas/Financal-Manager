"""User menu controller"""
from ui.controllers.base_controller import BaseViewController
from ui.components import MenuButton
from config.settings import UIConfig


class UserMenuController(BaseViewController):
    """Controller for the main user menu"""
    
    def show(self):
        self.clear_widgets()
        self.master.title(f"Finance Manager - {self.manager.current_username}")
        
        # Store buttons for navigation
        self.buttons = []
        self.current_button_index = 0
        
        button_configs = [
            ("Deposit", self.on_deposit),
            ("Withdraw", self.on_withdraw),
            ("Transfer", self.on_transfer),
            ("Bulk Add Transactions", self.on_bulk_add),
            ("Summary", self.on_summary),
            ("Account", self.on_account)
        ]
        
        for text, command in button_configs:
            btn = MenuButton(self.master, text, command)
            btn.pack(pady=2)
            self.buttons.append(btn)
        
        # Highlight first button
        self._highlight_button(0)
        
        # Setup navigation
        self.setup_key_bindings()
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts for user menu"""
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
    
    def on_deposit(self):
        from ui.controllers.deposit_controller import DepositController
        self.transition_to(DepositController)
    
    def on_withdraw(self):
        from ui.controllers.withdraw_controller import WithdrawController
        self.transition_to(WithdrawController)
    
    def on_transfer(self):
        from ui.controllers.transfer_controller import TransferController
        self.transition_to(TransferController)

    def on_bulk_add(self):
        """Navigate to bulk add transactions"""
        from ui.controllers.bulk_transaction_controller import BulkTransactionController
        self.transition_to(BulkTransactionController)
        
    def on_summary(self):
        from ui.controllers.summary_controller import SummaryController
        self.transition_to(SummaryController)
    
    def on_account(self):
        from ui.controllers.account_controller import AccountController
        self.transition_to(AccountController)

    def cleanup(self):
        """Cleanup arrow key bindings"""
        navigation_keys = ['<Up>', '<Down>', '<Return>', '<Escape>']
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass
        super().cleanup()
