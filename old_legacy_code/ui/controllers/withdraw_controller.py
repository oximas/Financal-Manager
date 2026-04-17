"""Withdraw controller"""
from datetime import datetime
from ui.controllers.base_controller import BaseViewController
from ui.components import CenteredForm, FormBuilder, MessageHelper
from config.settings import UIConfig
from core.result_types import TransactionSuccess
from utils.focus_manager import NavigationMode


class WithdrawController(BaseViewController):
    """Controller for withdraw screen"""
    
    def show(self):
        """Display the withdraw view."""
        self.clear_widgets()
        self.master.title("Withdraw Menu")
        
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Withdraw Menu") \
            .add_field("amount", "Money Amount:", placeholder="Enter amount") \
            .add_field(
                "category",
                "Category:",
                field_type="combobox",
                values=self.manager.get_category_names(),
                default_value=self.manager.get_category_names()[0] if self.manager.get_category_names() else "None"
            ) \
            .add_field("description", "Description:", placeholder="Enter description") \
            .add_field("quantity", "Quantity:", placeholder="Enter quantity") \
            .add_field(
                "unit",
                "Unit:",
                field_type="combobox",
                values=self.manager.get_unit_names(),
                default_value=self.manager.get_unit_names()[0] if self.manager.get_unit_names() else "None"
            ) \
            .add_field(
                "vault",
                "Vault:",
                field_type="combobox",
                values=self.manager.get_current_user_vault_names(),
                default_value="Main"
            ) \
            .add_field("date", "Date:", field_type="date")
        
        self.form.add_button(
            "Withdraw",
            self.on_submit,
            UIConfig.COLOR_PRIMARY,
            UIConfig.COLOR_TEXT_DARK
        ) \
        .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for withdraw screen."""
        self.focus_manager.enable_navigation(
            mode=NavigationMode.FORM,
            on_submit=self.on_submit,
            on_back=self.on_back
        )
    
    def on_submit(self):
        """Handle withdraw submission."""
        values = self.form.get_values()
        
        # Get date with time
        date_str = values.get("date")
        if date_str:
            date_str = date_str + " " + datetime.now().strftime("%H:%M:%S")
        else:
            date_str = None
        
        result = self.manager.process_withdraw(
            vault=values["vault"],
            amount=float(values["amount"]),
            category=values["category"],
            description=values["description"],
            quantity=float(values.get("quantity")),  # type:ignore
            unit=values.get("unit"),
            date=date_str
        )
        
        if isinstance(result, TransactionSuccess):
            MessageHelper.show_info(
                "Success",
                f"Withdraw of {result.amount:.2f} EGP was successful"
            )
        else:
            MessageHelper.show_error(
                "Transaction Failed",
                result.message
            )
    
    def on_back(self):
        """Navigate back to user menu."""
        from ui.controllers.user_menu_controller import UserMenuController
        self.transition_to(UserMenuController)
