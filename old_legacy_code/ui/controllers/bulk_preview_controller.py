"""Bulk preview controller"""
import customtkinter as ctk
from typing import List
from ui.controllers.base_controller import BaseViewController
from ui.components import MenuButton, MessageHelper
from config.settings import UIConfig


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
        self.master.bind('<Return>', lambda e: (self.on_confirm(), "break")[1])
        self.master.bind('<Escape>', lambda e: (self.on_back(), "break")[1])
    
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
        
        from ui.controllers.user_menu_controller import UserMenuController
        self.transition_to(UserMenuController)
    
    def on_back(self):
        """Go back to bulk entry screen"""
        from ui.controllers.bulk_transaction_controller import BulkTransactionController
        self.transition_to(BulkTransactionController)
