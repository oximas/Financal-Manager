# view_controllers.py
"""View controllers for different screens"""
import customtkinter as ctk
from typing import Callable
from datetime import datetime
from config import UIConfig
from ui_components import *
from result_types import *


class BaseViewController:
    """Base class for all view controllers"""
    
    def __init__(self, master: ctk.CTk, manager, database):
        self.master = master
        self.manager = manager
        self.database = database
        self.widgets = []
    
    def clear_widgets(self):
        """Remove all widgets from the screen"""
        for widget in self.master.winfo_children():
            widget.destroy()
        self.widgets.clear()
    
    def show(self):
        """Display this view (to be overridden)"""
        raise NotImplementedError


class MainMenuController(BaseViewController):
    """Controller for the main welcome screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Finance Manager - Welcome")
        
        login_btn = MenuButton(
            self.master,
            "Login",
            self.on_login_clicked
        )
        login_btn.pack(pady=10)
        
        signup_btn = MenuButton(
            self.master,
            "Sign Up",
            self.on_signup_clicked
        )
        signup_btn.pack(pady=10)
    
    def on_login_clicked(self):
        from view_factory import ViewFactory
        ViewFactory.show_login(self.master, self.manager, self.database)
    
    def on_signup_clicked(self):
        from view_factory import ViewFactory
        ViewFactory.show_signup(self.master, self.manager, self.database)


class LoginController(BaseViewController):
    """Controller for the login screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Login")
        
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Login") \
            .add_field("username", "Username:", placeholder="Enter username") \
            .add_field("password", "Password:", placeholder="Enter password", show="*") \
            .add_button("Login", self.on_login, UIConfig.COLOR_PRIMARY, UIConfig.COLOR_TEXT_DARK) \
            .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
    
    def on_login(self):
        values = self.form.get_values()
        result: AuthResult = self.manager.login(
            values["username"],
            values["password"]
        )
        
        if isinstance(result, AuthSuccess):
            from view_factory import ViewFactory
            ViewFactory.show_user_menu(self.master, self.manager, self.database)
        else:  # AuthFailure
            MessageHelper.show_error("Login Failed", result.message)
    
    def on_back(self):
        from view_factory import ViewFactory
        ViewFactory.show_main_menu(self.master, self.manager, self.database)


class SignupController(BaseViewController):
    """Controller for the signup screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Sign Up")
        
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Sign Up") \
            .add_field("username", "Username:", placeholder="Enter username") \
            .add_field("password", "Password:", placeholder="Enter password", show="*") \
            .add_field("confirm_password", "Confirm Password:", placeholder="Confirm password", show="*") \
            .add_button("Sign Up", self.on_signup, UIConfig.COLOR_PRIMARY, UIConfig.COLOR_TEXT_DARK) \
            .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
    
    def on_signup(self):
        values = self.form.get_values()
        result: AuthResult = self.manager.signup(
            values["username"],
            values["password"],
            values["confirm_password"]
        )
        
        if isinstance(result, AuthSuccess): #maybe use the functions from result type instead ???
            from view_factory import ViewFactory
            ViewFactory.show_user_menu(self.master, self.manager, self.database)
        else:
            MessageHelper.show_error("Signup Failed", result.message)
    
    def on_back(self):
        from view_factory import ViewFactory
        ViewFactory.show_main_menu(self.master, self.manager, self.database)


class UserMenuController(BaseViewController):
    """Controller for the main user menu"""
    
    def show(self):
        self.clear_widgets()
        self.master.title(f"Finance Manager - {self.manager.current_username}")
        
        buttons = [
            ("Deposit", self.on_deposit),
            ("Withdraw", self.on_withdraw),
            ("Transfer", self.on_transfer),
            ("Summary", self.on_summary),
            ("Account", self.on_account)
        ]
        
        for text, command in buttons:
            btn = MenuButton(self.master, text, command)
            btn.pack(pady=2)
    
    def on_deposit(self):
        from view_factory import ViewFactory
        ViewFactory.show_transaction(self.master, self.manager, self.database, "Deposit")
    
    def on_withdraw(self):
        from view_factory import ViewFactory
        ViewFactory.show_transaction(self.master, self.manager, self.database, "Withdraw")
    
    def on_transfer(self):
        from view_factory import ViewFactory
        ViewFactory.show_transfer(self.master, self.manager, self.database)
    
    def on_summary(self):
        from view_factory import ViewFactory
        ViewFactory.show_summary(self.master, self.manager, self.database)
    
    def on_account(self):
        from view_factory import ViewFactory
        ViewFactory.show_account(self.master, self.manager, self.database)


class TransactionController(BaseViewController):
    """Controller for deposit/withdraw screens"""
    
    def __init__(self, master, manager, database, transaction_type: str):
        super().__init__(master, manager, database)
        self.transaction_type = transaction_type
    
    def show(self):
        self.clear_widgets()
        self.master.title(f"{self.transaction_type} Menu")
        
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title(f"{self.transaction_type} Menu") \
            .add_field("amount", "Money Amount:", placeholder="Enter amount") \
            .add_field(
                "category",
                "Category:",
                field_type="combobox",
                values=self.database.get_category_names(),
                default_value=self.database.get_category_names()[0] if self.database.get_category_names() else "None"
            ) \
            .add_field("description", "Description:", placeholder="Enter description")
        
        # Add withdraw-specific fields
        if self.transaction_type == "Withdraw":
            self.form.add_field("quantity", "Quantity:", placeholder="Enter quantity") \
                .add_field(
                    "unit",
                    "Unit:",
                    field_type="combobox",
                    values=self.database.get_unit_names(),
                    default_value=self.database.get_unit_names()[0] if self.database.get_unit_names() else "None"
                )
        
        # Add vault selection
        self.form.add_field(
            "vault",
            "Vault:",
            field_type="combobox",
            values=self.manager.get_vault_names(),
            default_value="Main"
        ) \
        .add_field("date", "Date:", field_type="date")
        
        self.form.add_button(
            self.transaction_type,
            self.on_submit,
            UIConfig.COLOR_PRIMARY,
            UIConfig.COLOR_TEXT_DARK
        ) \
        .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
    
    def on_submit(self):
        values = self.form.get_values()
        
        # Get date with time
        date_str = values.get("date")
        if date_str:
            date_str = date_str + " " + datetime.now().strftime("%H:%M:%S")
        else:
            date_str = None
        
        if self.transaction_type == "Deposit":
            result: TransactionResult = self.manager.process_deposit(
                vault=values["vault"],
                amount=values["amount"],
                category=values["category"],
                description=values["description"],
                date=date_str
            )
        else:  # Withdraw
            result: TransactionResult = self.manager.process_withdraw(
                vault=values["vault"],
                amount=values["amount"],
                category=values["category"],
                description=values["description"],
                quantity=values.get("quantity"),
                unit=values.get("unit"),
                date=date_str
            )
        
        if isinstance(result, TransactionSuccess):
            MessageHelper.show_info(
                "Success",
                f"{self.transaction_type} of {result.amount:.2f} EGP was successful"
            )
        else:
            MessageHelper.show_error(
                "Transaction Failed",
                result.message
            )
    
    def on_back(self):
        from view_factory import ViewFactory
        ViewFactory.show_user_menu(self.master, self.manager, self.database)


class TransferController(BaseViewController):
    """Controller for transfer screen"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Transfer Menu")
        
        form_frame = CenteredForm(self.master)
        
        from_vault_names = self.manager.get_vault_names()
        
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
                values=self.database.get_usernames(),
                default_value=self.manager.current_username
            ) \
            .add_field(
                "to_vault",
                "To Vault:",
                field_type="combobox",
                values=self.manager.get_vault_names(),
                default_value="Main"
            ) \
            .add_field("amount", "Amount:", placeholder="Enter amount") \
            .add_field("reason", "Reason (optional):", placeholder="Enter reason") \
            .add_button("Transfer", self.on_submit, UIConfig.COLOR_PRIMARY, UIConfig.COLOR_TEXT_DARK) \
            .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
        
        # Setup dynamic vault update when user changes
        to_user_widget = self.form.fields["to_user"].widget
        to_user_widget.configure(command=self.on_user_changed)
    
    def on_user_changed(self, selected_user: str):
        """Update the to_vault options when user selection changes"""
        to_vault_names = self.database.get_user_vault_names(selected_user)
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
            amount=values["amount"],
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
        from view_factory import ViewFactory
        ViewFactory.show_user_menu(self.master, self.manager, self.database)


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
        
        vaults = self.manager.get_vaults()
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
    
    def on_back(self):
        from view_factory import ViewFactory
        ViewFactory.show_user_menu(self.master, self.manager, self.database)


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
        
        # Action buttons
        buttons = [
            ("Add Vault", self.on_add_vault, "secondary"),
            ("Change Password", self.on_change_password, "secondary"),
            ("Export data to Excel", self.on_export_excel, "secondary"),
            ("Logout", self.on_logout, "primary"),
            ("Back", self.on_back, "back")
        ]
        
        for text, command, btn_type in buttons:
            btn = MenuButton(self.master, text, command, btn_type)
            btn.pack(pady=2)
    
    def on_add_vault(self):
        ask_dialog = ctk.CTkInputDialog(
            text="New vault name is:",
            title="Add new vault"
        )
        new_vault_name = ask_dialog.get_input()
        
        if new_vault_name:
            try:
                self.database.add_vault(self.manager.current_username, new_vault_name)
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
            self.database.export_to_excel(self.manager.current_username)
            MessageHelper.show_info("Success", "Data exported successfully!")
        except PermissionError:
            MessageHelper.show_error(
                "Export Failed",
                "Please close any instances of the file and make sure you have write permissions"
            )
        except Exception as e:
            MessageHelper.show_error("Export Failed", str(e))
    
    def on_logout(self):
        self.manager.logout()
        from view_factory import ViewFactory
        ViewFactory.show_main_menu(self.master, self.manager, self.database)
    
    def on_back(self):
        from view_factory import ViewFactory
        ViewFactory.show_user_menu(self.master, self.manager, self.database)