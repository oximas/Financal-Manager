"""ui/controllers/bulk_transaction_controller.py"""
import customtkinter as ctk
from typing import List
from ui.controllers import BaseViewController,  UserMenuController
from ui.components import MenuButton, MessageHelper
from config.settings import UIConfig


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
            user_names=self.manager.get_usernames(),
            on_last_row_enter=lambda: print("not implemented")
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
