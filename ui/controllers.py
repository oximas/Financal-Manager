"""View controllers for different screens"""
from core.manager import Manager
import customtkinter as ctk
from typing import Type, List
from datetime import datetime
from config.settings import UIConfig
from ui.components import *
from core.result_types import *
from core.bulk_processor import TransactionRow
from utils.key_bindings import KeyBindingManager, KeyAction


class BaseViewController:
    """
    Base class for all view controllers.
    Handles widget management and keyboard shortcuts.
    """
    
    def __init__(self, master: ctk.CTk, manager: Manager):
        """
        Initialize the base view controller.
        
        Args:
            master: The root tkinter window
            manager: The business logic manager
        """
        self.master = master
        self.manager = manager
        self.widgets = []
        
        # Initialize key binding manager
        self.key_manager = KeyBindingManager(master)
        
        # CRITICAL: Unbind ALL previous bindings when creating new controller
        self._unbind_all_navigation_keys()
    
    def _unbind_all_navigation_keys(self):
        """Unbind all navigation keys from previous controllers"""
        navigation_keys = [
            '<Up>', '<Down>', '<Left>', '<Right>',
            '<Return>', '<Tab>', '<Shift-Tab>'
        ]
        
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass

    def clear_widgets(self) -> None:
        """Remove all widgets from the screen."""
        for widget in self.master.winfo_children():
            widget.destroy()
        self.widgets.clear()
    
    def setup_key_bindings(self) -> None:
        """
        Setup keyboard shortcuts for this view.
        Override this method in child classes to define view-specific bindings.
        
        Example:
            def setup_key_bindings(self):
                self.key_manager.bind_multiple([
                    (KeyAction.SUBMIT, self.on_submit),
                    (KeyAction.BACK, self.on_back)
                ])
        """
        pass
    
    def cleanup(self) -> None:
        """
        Cleanup resources when leaving this view.
        Automatically unbinds all key bindings.
        Override to add additional cleanup logic.
        """
        self.key_manager.unbind_all()
    
    def _resize_window(self):
        """Resize window to fit content"""
        self.master.update_idletasks()
        width = self.master.winfo_reqwidth()
        height = self.master.winfo_reqheight()
        margin = UIConfig.WINDOW_MARGIN

        new_width = max(width + margin, UIConfig.DEFAULT_WIDTH)
        new_height = max(height + margin, UIConfig.DEFAULT_HEIGHT)
        
        self.master.geometry(f"{new_width}x{new_height}")
    
    def show(self) -> None:
        """
        Display this view.
        Must be overridden by child classes.
        """
        raise NotImplementedError("Subclasses must implement show()")
    
    def transition_to(self, view_controller:Type["BaseViewController"]) -> None:
        """
        Helper method to transition to another view with proper cleanup.
        
        Args:
            view_controller: The view controller class to transition to
        
        Example:
            self.transition_to(LoginController)
        """
        self.cleanup()
        view_controller(self.master, self.manager).show()
        self._resize_window()


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
        # Up/Down navigation
        self.master.bind('<Up>', lambda e: self._navigate_buttons(-1))
        self.master.bind('<Down>', lambda e: self._navigate_buttons(1))
        self.master.bind('<Return>', lambda e: self._activate_current_button())
        
        # Ctrl+Backspace does nothing on main menu (can't go back)
        self.key_manager.bind(KeyAction.BACK, lambda: None)
    
    def _navigate_buttons(self, direction):
        """Navigate through buttons with arrow keys"""
        # Remove highlight from current
        self._unhighlight_button(self.current_button_index)
        
        # Move index (with looping)
        self.current_button_index = (self.current_button_index + direction) % len(self.buttons)
        
        # Highlight new button
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
        self.transition_to(LoginController)
    
    def on_signup_clicked(self):
        self.transition_to(SignupController)

    def cleanup(self):
        """Cleanup arrow key bindings"""
        navigation_keys = ['<Up>', '<Down>', '<Return>']
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass
        super().cleanup()


class LoginController(BaseViewController):
    """Controller for the login screen"""
    
    def show(self):
        """Display the login view."""
        self.clear_widgets()
        self.master.title("Login")
        
        # Create the GUI
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Login") \
            .add_field("username", "Username:", placeholder="Enter username") \
            .add_field("password", "Password:", placeholder="Enter password", show="*") \
            .add_button("Login", self.on_submit, UIConfig.COLOR_PRIMARY, UIConfig.COLOR_TEXT_DARK) \
            .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for login screen."""
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_submit),  # Shift+Enter
            (KeyAction.BACK, self.on_back)
        ])
    
    def on_submit(self):
        """Handle login submission."""
        values = self.form.get_values()
        result = self.manager.login(
            values["username"],
            values["password"]
        )
        
        if isinstance(result, AuthSuccess):
            self.transition_to(UserMenuController)
        else:
            MessageHelper.show_error("Login Failed", result.message)
    
    def on_back(self):
        """Navigate back to main menu."""
        self.transition_to(MainMenuController)


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
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_submit),
            (KeyAction.BACK, self.on_back)
        ])
    
    def on_submit(self):
        """Handle signup submission."""
        values = self.form.get_values()
        result = self.manager.signup(
            values["username"],
            values["password"],
            values["confirm_password"]
        )
        
        if isinstance(result, AuthSuccess):
            self.transition_to(UserMenuController)
        else:
            MessageHelper.show_error("Signup Failed", result.message)
    
    def on_back(self):
        """Navigate back to main menu."""
        self.transition_to(MainMenuController)


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
            ("Bulk Add Transactions", self.on_bulk_add),  # NEW
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
        # Up/Down navigation
        self.master.bind('<Up>', lambda e: self._navigate_buttons(-1))
        self.master.bind('<Down>', lambda e: self._navigate_buttons(1))
        self.master.bind('<Return>', lambda e: self._activate_current_button())
        
        # Ctrl+Backspace does nothing (can't go back after login)
        self.key_manager.bind(KeyAction.BACK, lambda: None)
    
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
        self.transition_to(DepositController)
    
    def on_withdraw(self):
        self.transition_to(WithdrawController)
    
    def on_transfer(self):
        self.transition_to(TransferController)

    def on_bulk_add(self):
        """Navigate to bulk add transactions"""
        self.transition_to(BulkTransactionController)
        
    def on_summary(self):
        self.transition_to(SummaryController)
    
    def on_account(self):
        self.transition_to(AccountController)

    def cleanup(self):
        """Cleanup arrow key bindings"""
        navigation_keys = ['<Up>', '<Down>', '<Return>']
        for key in navigation_keys:
            try:
                self.master.unbind(key)
            except:
                pass
        super().cleanup()


class DepositController(BaseViewController):
    """Controller for deposit screen"""
    
    def show(self):
        """Display the deposit view."""
        self.clear_widgets()
        self.master.title("Deposit Menu")
        
        form_frame = CenteredForm(self.master)
        
        self.form = FormBuilder(form_frame)
        self.form.add_title("Deposit Menu") \
            .add_field("amount", "Money Amount:", placeholder="Enter amount") \
            .add_field(
                "category",
                "Category:",
                field_type="combobox",
                values=self.manager.get_category_names(),
                default_value=self.manager.get_category_names()[0] if self.manager.get_category_names() else "None"
            ) \
            .add_field("description", "Description:", placeholder="Enter description") \
            .add_field(
                "vault",
                "Vault:",
                field_type="combobox",
                values=self.manager.get_current_user_vault_names(),
                default_value="Main"
            ) \
            .add_field("date", "Date:", field_type="date")
        
        self.form.add_button(
            "Deposit",
            self.on_submit,
            UIConfig.COLOR_PRIMARY,
            UIConfig.COLOR_TEXT_DARK
        ) \
        .add_button("Back", self.on_back, UIConfig.COLOR_SECONDARY, UIConfig.COLOR_TEXT_PRIMARY)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self) -> None:
        """Setup keyboard shortcuts for deposit screen."""
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_submit),
            (KeyAction.BACK, self.on_back),
            (KeyAction.CANCEL, self.on_back)
        ])
    
    def on_submit(self):
        """Handle deposit submission."""
        values = self.form.get_values()
        
        # Get date with time
        date_str = values.get("date")
        if date_str:
            date_str = date_str + " " + datetime.now().strftime("%H:%M:%S")
        else:
            date_str = None
        
        result = self.manager.process_deposit(
            vault=values["vault"],
            amount=float(values["amount"]),
            category=values["category"],
            description=values["description"],
            date=date_str
        )
        
        if isinstance(result, TransactionSuccess):
            MessageHelper.show_info(
                "Success",
                f"Deposit of {result.amount:.2f} EGP was successful"
            )
        else:
            MessageHelper.show_error(
                "Transaction Failed",
                result.message
            )
    
    def on_back(self):
        """Navigate back to user menu."""
        self.transition_to(UserMenuController)


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
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_submit),
            (KeyAction.BACK, self.on_back),
            (KeyAction.CANCEL, self.on_back)
        ])
    
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
        self.transition_to(UserMenuController)


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
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_submit),  # Shift+Enter
            (KeyAction.BACK, self.on_back)
        ])
    
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
        self.transition_to(UserMenuController)


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
        self.key_manager.bind(KeyAction.BACK, self.on_back)
    
    def on_back(self):
        self.transition_to(UserMenuController)


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
        # Up/Down navigation
        self.master.bind('<Up>', lambda e: self._navigate_buttons(-1))
        self.master.bind('<Down>', lambda e: self._navigate_buttons(1))
        self.master.bind('<Return>', lambda e: self._activate_current_button())
        
        # Ctrl+Backspace for back
        self.key_manager.bind(KeyAction.BACK, self.on_back)
    
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
        self.transition_to(MainMenuController)
    
    def on_back(self):
        self.transition_to(UserMenuController)
class BulkTransactionController(BaseViewController):
    """Controller for bulk transaction entry"""
    
    def show(self):
        self.clear_widgets()
        self.master.title("Bulk Add Transactions")
        
        # Main container
        container = ctk.CTkFrame(self.master, fg_color=UIConfig.COLOR_BACKGROUND)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            container,
            text="Bulk Add Transactions",
            font=UIConfig.FONT_TITLE,
            text_color=UIConfig.COLOR_TEXT_DARK
        )
        title.pack(pady=(10, 20))
        
        # Row count selector
        row_control_frame = ctk.CTkFrame(container, fg_color=UIConfig.COLOR_FRAME_LIGHT)
        row_control_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            row_control_frame,
            text="Number of Rows:",
            font=UIConfig.FONT_NORMAL
        ).pack(side="left", padx=10)
        
        self.row_count_var = ctk.StringVar(value="5")
        row_count_combo = ctk.CTkComboBox(
            row_control_frame,
            variable=self.row_count_var,
            values=["5", "10", "15", "20", "25", "30"],
            width=100
        )
        row_count_combo.pack(side="left", padx=5)
        
        # Bind Enter key to generate rows button
        row_count_combo.bind('<Return>', lambda e: self.on_generate_rows())
        
        generate_btn = ctk.CTkButton(
            row_control_frame,
            text="Generate Rows",
            command=self.on_generate_rows,
            fg_color=UIConfig.COLOR_SECONDARY,
            width=120
        )
        generate_btn.pack(side="left", padx=10)
        
        # Transaction grid
        from ui.bulk_components import BulkTransactionGrid
        
        self.grid = BulkTransactionGrid(
            container,
            initial_rows=5,
            vault_names=self.manager.get_current_user_vault_names(),
            category_names=self.manager.get_category_names(),
            unit_names=self.manager.get_unit_names(),
            user_names=self.manager.get_usernames()
        )
        self.grid.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add row button
        add_row_btn = ctk.CTkButton(
            container,
            text="+",
            command=self.on_add_row,
            fg_color=UIConfig.COLOR_SUCCESS,
            width=50,
            font=UIConfig.FONT_HEADING
        )
        add_row_btn.pack(pady=5)
        
        # Error display
        self.error_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=UIConfig.COLOR_FRAME_DARK,
            height=100
        )
        self.error_frame.pack(fill="x", padx=10, pady=5)
        
        self.error_label = ctk.CTkLabel(
            self.error_frame,
            text="",
            font=UIConfig.FONT_NORMAL,
            text_color=UIConfig.COLOR_TEXT_SECONDARY,
            justify="left"
        )
        self.error_label.pack(pady=5, padx=10, anchor="w")
        
        # Action buttons
        button_frame = ctk.CTkFrame(container, fg_color=UIConfig.COLOR_BACKGROUND)
        button_frame.pack(pady=10)
        
        MenuButton(
            button_frame,
            "Validate",
            self.on_validate,
            "secondary"
        ).pack(side="left", padx=5)
        
        self.confirm_btn = MenuButton(
            button_frame,
            "Preview & Confirm",
            self.on_preview,
            "primary"
        )
        self.confirm_btn.pack(side="left", padx=5)
        self.confirm_btn.configure(state="disabled")  # Disabled until validated
        
        MenuButton(
            button_frame,
            "Back",
            self.on_back,
            "back"
        ).pack(side="left", padx=5)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
        
        # Store validation result
        self.validation_result = None
    def _resize_window(self):
        self.master.state('zoomed')
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_validate),
            (KeyAction.BACK, self.on_back),
            (KeyAction.CANCEL, self.on_back)
        ])
    
    def cleanup(self):
        """Cleanup: unbind arrow keys from previous screen"""
        # Unbind arrow keys that might be lingering from UserMenuController
        try:
            self.master.unbind('<Up>')
            self.master.unbind('<Down>')
            self.master.unbind('<Return>')
        except:
            pass
        
        super().cleanup()
    
    def on_generate_rows(self):
        """Regenerate grid with new row count"""
        try:
            new_count = int(self.row_count_var.get())
            self.grid.regenerate_rows(new_count)
            self.error_label.configure(text="")
            self.validation_result = None
            self.confirm_btn.configure(state="disabled")
        except ValueError:
            MessageHelper.show_error("Error", "Invalid row count")
    
    def on_add_row(self):
        """Add a single row to the grid"""
        self.grid.add_row()
        self.error_label.configure(text="")
        self.validation_result = None
        self.confirm_btn.configure(state="disabled")
    
    def on_validate(self):
        """Validate all transactions"""
        from core.bulk_processor import BulkTransactionValidator
        
        # Get all rows
        rows = self.grid.get_all_rows()
        
        # Validate
        validator = BulkTransactionValidator(self.manager.db)
        self.validation_result = validator.validate_batch(
            rows,
            self.manager.current_username
        )
        
        # Display results
        if self.validation_result.is_valid:
            self.error_label.configure(
                text=f"✓ {self.validation_result.error_summary}",
                text_color=UIConfig.COLOR_SUCCESS
            )
            self.confirm_btn.configure(state="normal")
        else:
            # Format errors
            error_text = f"✗ {self.validation_result.error_summary}\n\n"
            for error in self.validation_result.errors:
                error_text += f"Row {error.row_number}, {error.field}: {error.message}\n"
            
            self.error_label.configure(
                text=error_text,
                text_color="#FF6B6B"
            )
            self.confirm_btn.configure(state="disabled")
    
    def on_preview(self):
        """Show preview screen"""
        if not self.validation_result or not self.validation_result.is_valid:
            MessageHelper.show_warning(
                "Validation Required",
                "Please validate transactions first"
            )
            return
        
        self.transition_to(lambda master, manager: BulkPreviewController(
            master,
            manager,
            self.grid.get_all_rows()
        ))
    
    def on_back(self):
        """Go back to user menu"""
        self.transition_to(UserMenuController)


class BulkPreviewController(BaseViewController):
    """Controller for previewing bulk transactions before confirmation"""
    
    def __init__(self, master, manager, rows: List):
        self.rows = rows
        super().__init__(master, manager)
    
    def show(self):
        self.clear_widgets()
        self.master.title("Preview Transactions")
        
        # Main container
        container = ctk.CTkFrame(self.master, fg_color=UIConfig.COLOR_BACKGROUND)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            container,
            text="Preview & Confirm Transactions",
            font=UIConfig.FONT_TITLE,
            text_color=UIConfig.COLOR_TEXT_DARK
        )
        title.pack(pady=(10, 20))
        
        # Preview table
        from ui.bulk_components import PreviewTable
        
        preview = PreviewTable(container, self.rows)
        preview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Action buttons
        button_frame = ctk.CTkFrame(container, fg_color=UIConfig.COLOR_BACKGROUND)
        button_frame.pack(pady=20)
        
        MenuButton(
            button_frame,
            "Back",
            self.on_back,
            "secondary"
        ).pack(side="left", padx=5)
        
        MenuButton(
            button_frame,
            "Confirm & Save",
            self.on_confirm,
            "primary"
        ).pack(side="left", padx=5)
        
        # Setup keyboard shortcuts
        self.setup_key_bindings()
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        self.key_manager.bind_multiple([
            (KeyAction.SUBMIT, self.on_confirm),
            (KeyAction.BACK, self.on_back),
            (KeyAction.CANCEL, self.on_back)
        ])
    
    def on_confirm(self):
        """Process all transactions"""
        from core.bulk_processor import BulkTransactionProcessor
        
        processor = BulkTransactionProcessor(self.manager)
        successful, failed = processor.process_batch(self.rows)
        
        if failed == 0:
            MessageHelper.show_info(
                "Success",
                f"Successfully processed {successful} transactions!"
            )
        else:
            MessageHelper.show_warning(
                "Partial Success",
                f"Processed {successful} transactions, {failed} failed"
            )
        
        self.transition_to(UserMenuController)
    
    def on_back(self):
        """Go back to bulk entry screen"""
        # Note: This will lose data. In production, you might want to preserve it
        self.transition_to(BulkTransactionController)