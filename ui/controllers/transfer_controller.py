"""Transfer controller"""
from ui.controllers.base_controller import BaseViewController
from ui.components import CenteredForm, FormBuilder, MessageHelper
from config.settings import UIConfig
from core.result_types import TransactionResult, TransactionSuccess
from utils.focus_manager import NavigationMode


class TransferController(BaseViewController):
    """Controller for transfer screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Transfer Menu")
        
        form_frame = CenteredForm(self.master)
        
        from_vault_names = self.manager.get_current_user_vault_names()
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Transfer Menu") \
            .add_field(
                "from_vault",
                "From:",
                field_type="combobox",
                values=from_vault_names,
                default_value=from_vault_names[0] if from_vault_names else "Main"
            ) \
            .add_field(
                "to_user",
                "To User:",
                field_type="combobox",
                values=self.manager.get_usernames(),
                default_value=self.manager.current_username
            ) \
            .add_field(
                "to_vault",
                "To Vault:",
                field_type="combobox",
                values=self.manager.get_current_user_vault_names(),
                default_value="Main"
            ) \
            .add_field("amount", "Amount:", placeholder="Enter amount") \
            .add_field("reason", "Reason (optional):", placeholder="Enter reason") \
            .add_button("Transfer", self.on_submit, UIConfig.COLOR_PRIMARY, UIConfig.COLOR_TEXT_DARK) \
            .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
        
        # Setup dynamic vault update when user changes
        to_user_widget = self.form.fields["to_user"].widget
        to_user_widget.configure(command=self.on_user_changed)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for transfer screen."""
        self.focus_manager.enable_navigation(
            mode=NavigationMode.FORM,
            on_submit=self.on_submit,
            on_back=self.on_back
        )
    
    def on_user_changed(self, selected_user: str):
        """Update the to_vault options when user selection changes"""
        to_vault_names = self.manager.get_user_vault_names(selected_user)
        to_vault_field = self.form.fields["to_vault"]
        
        if to_vault_names:
            to_vault_field.variable.set(to_vault_names[0])
            to_vault_field.widget.configure(values=to_vault_names)
        else:
            to_vault_field.variable.set("No Vaults Available")
            to_vault_field.widget.configure(values=["No Vaults Available"])
    
    def on_submit(self):
        values = self.form.get_values()
        
        result: TransactionResult = self.manager.process_transfer(
            from_vault=values["from_vault"],
            to_user=values["to_user"],
            to_vault=values["to_vault"],
            amount=float(values["amount"]),
            reason=values["reason"] if values["reason"] else None
        )
        
        if isinstance(result, TransactionSuccess):
            MessageHelper.show_info(
                "Success",
                f"Transfer of {result.amount:.2f} EGP was successful"
            )
        else:
            MessageHelper.show_error("Transfer Failed", result.message)
    
    def on_back(self):
        from ui.controllers.user_menu_controller import UserMenuController
        self.transition_to(UserMenuController)
