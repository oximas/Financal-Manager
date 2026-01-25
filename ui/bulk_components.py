# ui/bulk_components.py
"""
UI components for bulk transaction entry.
Provides editable grid with Excel-like navigation.
"""
import customtkinter as ctk
from typing import List, Dict, Callable, Optional, Any
from CTkTable import CTkTable
from config.settings import UIConfig
from core.bulk_processor import TransactionRow
from CTkDatePicker import CTkDatePicker


class BulkTransactionGrid(ctk.CTkFrame):
    """
    Editable grid for bulk transaction entry with unified column layout.
    All columns are always visible, fields are enabled/disabled based on transaction type.
    """
    
    # Unified column layout (all possible columns)
    COLUMNS = [
        ("Type", 100),
        ("Vault", 120),
        ("Amount", 100),
        ("Category", 120),
        ("Description", 180),
        ("Quantity", 80),
        ("Unit", 100),
        ("To User", 120),
        ("To Vault", 120),
        ("Date", 140)
    ]
    
    def __init__(
        self,
        parent,
        initial_rows: int,
        vault_names: List[str],
        category_names: List[str],
        unit_names: List[str],
        user_names: List[str]
    ):
        super().__init__(parent)
        
        self.vault_names = vault_names
        self.category_names = category_names
        self.unit_names = unit_names
        self.user_names = user_names
        
        self.row_count = initial_rows
        self.row_widgets: List[Dict[str, Any]] = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the grid UI"""
        # Scrollable container for rows
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=UIConfig.COLOR_FRAME_DARK
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Build header and rows
        self._build_header()
        self._build_rows()
    
    def _build_header(self):
        """Build column headers"""
        header_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=UIConfig.COLOR_SECONDARY
        )
        header_frame.pack(fill="x", pady=(0, 5))
        
        for i, (col_name, width) in enumerate(self.COLUMNS):
            label = ctk.CTkLabel(
                header_frame,
                text=col_name,
                font=UIConfig.FONT_NORMAL,
                width=width
            )
            label.grid(row=0, column=i, padx=2, pady=5, sticky="ew")
    
    def _build_rows(self):
        """Build data entry rows"""
        self.row_widgets.clear()
        
        for row_num in range(self.row_count):
            row_frame = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=UIConfig.COLOR_FRAME_LIGHT
            )
            row_frame.pack(fill="x", pady=2)
            
            widgets = self._build_row_widgets(row_frame, row_num)
            self.row_widgets.append(widgets)
    
    def _build_row_widgets(
        self,
        parent: ctk.CTkFrame,
        row_num: int
    ) -> Dict[str, Any]:
        """Build widgets for a single row (all columns)"""
        widgets = {"row_number": row_num + 1}
        col = 0
        
        # Transaction Type
        type_var = ctk.StringVar(value="")
        type_combo = ctk.CTkComboBox(
            parent,
            variable=type_var,
            values=["Deposit", "Withdraw", "Transfer"],
            width=100,
            command=lambda v, r=row_num: self._on_type_change(r, v)
        )
        type_combo.grid(row=0, column=col, padx=2, pady=2)
        widgets["type"] = type_var
        widgets["type_widget"] = type_combo
        col += 1
        
        # Vault
        vault_var = ctk.StringVar(value="")
        vault_combo = ctk.CTkComboBox(
            parent,
            variable=vault_var,
            values=self.vault_names,
            width=120
        )
        vault_combo.grid(row=0, column=col, padx=2, pady=2)
        widgets["vault"] = vault_var
        widgets["vault_widget"] = vault_combo
        col += 1
        
        # Amount
        amount_var = ctk.StringVar(value="")
        amount_entry = ctk.CTkEntry(parent, textvariable=amount_var, width=100)
        amount_entry.grid(row=0, column=col, padx=2, pady=2)
        widgets["amount"] = amount_var
        widgets["amount_widget"] = amount_entry
        col += 1
        
        # Category
        category_var = ctk.StringVar(value="")
        category_combo = ctk.CTkComboBox(
            parent,
            variable=category_var,
            values=self.category_names,
            width=120
        )
        category_combo.grid(row=0, column=col, padx=2, pady=2)
        widgets["category"] = category_var
        widgets["category_widget"] = category_combo
        col += 1
        
        # Description
        desc_var = ctk.StringVar(value="")
        desc_entry = ctk.CTkEntry(parent, textvariable=desc_var, width=180)
        desc_entry.grid(row=0, column=col, padx=2, pady=2)
        widgets["description"] = desc_var
        widgets["description_widget"] = desc_entry
        col += 1
        
        # Quantity
        qty_var = ctk.StringVar(value="")
        qty_entry = ctk.CTkEntry(parent, textvariable=qty_var, width=80)
        qty_entry.grid(row=0, column=col, padx=2, pady=2)
        widgets["quantity"] = qty_var
        widgets["quantity_widget"] = qty_entry
        col += 1
        
        # Unit
        unit_var = ctk.StringVar(value="")
        unit_combo = ctk.CTkComboBox(
            parent,
            variable=unit_var,
            values=self.unit_names,
            width=100
        )
        unit_combo.grid(row=0, column=col, padx=2, pady=2)
        widgets["unit"] = unit_var
        widgets["unit_widget"] = unit_combo
        col += 1
        
        # To User
        to_user_var = ctk.StringVar(value="")
        to_user_combo = ctk.CTkComboBox(
            parent,
            variable=to_user_var,
            values=self.user_names,
            width=120
        )
        to_user_combo.grid(row=0, column=col, padx=2, pady=2)
        widgets["to_user"] = to_user_var
        widgets["to_user_widget"] = to_user_combo
        col += 1
        
        # To Vault
        to_vault_var = ctk.StringVar(value="")
        to_vault_combo = ctk.CTkComboBox(
            parent,
            variable=to_vault_var,
            values=self.vault_names,
            width=120
        )
        to_vault_combo.grid(row=0, column=col, padx=2, pady=2)
        widgets["to_vault"] = to_vault_var
        widgets["to_vault_widget"] = to_vault_combo
        col += 1
        
        # Date (with date picker)
        date_var = ctk.StringVar(value="")
        date_frame = ctk.CTkFrame(parent, fg_color="transparent")
        date_frame.grid(row=0, column=col, padx=2, pady=2)

        date_entry = ctk.CTkEntry(
            date_frame,
            textvariable=date_var,
            placeholder_text="YYYY-MM-DD",
            width=100
        )
        date_entry.pack(side="left", padx=(0, 2))

        # Date picker button
        def create_date_picker_callback(var):
            """Create a callback for date picker"""
            def on_date_click():
                # Create date picker window
                picker_window = ctk.CTkToplevel(self.master)
                picker_window.title("Select Date")
                picker_window.geometry("300x300")
                
                # Create date picker
                date_picker = CTkDatePicker(picker_window)
                date_picker.set_date_format("%Y-%m-%d")
                date_picker.pack(pady=20)
                
                # OK button
                def on_ok():
                    selected = date_picker.get_date()
                    if selected:
                        var.set(selected)
                    picker_window.destroy()
                
                ok_btn = ctk.CTkButton(
                    picker_window,
                    text="OK",
                    command=on_ok
                )
                ok_btn.pack(pady=10)
                
                # Cancel button
                cancel_btn = ctk.CTkButton(
                    picker_window,
                    text="Cancel",
                    command=picker_window.destroy
                )
                cancel_btn.pack(pady=5)
            
            return on_date_click

        date_btn = ctk.CTkButton(
            date_frame,
            text="📅",
            width=30,
            command=create_date_picker_callback(date_var)
        )
        date_btn.pack(side="left")

        widgets["date"] = date_var
        widgets["date_widget"] = date_entry
        
        # Initially disable all fields (until type is selected)
        self._update_field_states(row_num, "")
        
        return widgets
    
    def _on_type_change(self, row_num: int, value: str):
        """Handle transaction type change for a row"""
        self._update_field_states(row_num, value)
    
    def _update_field_states(self, row_num: int, tx_type: str):
        """Enable/disable fields based on transaction type"""
        if row_num >= len(self.row_widgets):
            return
        
        widgets = self.row_widgets[row_num]
        tx_type_lower = tx_type.lower()
        
        # Common fields (always enabled)
        self._set_widget_state(widgets.get("vault_widget"), True)
        self._set_widget_state(widgets.get("amount_widget"), True)
        self._set_widget_state(widgets.get("description_widget"), True)
        self._set_widget_state(widgets.get("date_widget"), True)
        
        if tx_type_lower == "deposit":
            # Enable: category
            # Disable: quantity, unit, to_user, to_vault
            self._set_widget_state(widgets.get("category_widget"), True)
            self._set_widget_state(widgets.get("quantity_widget"), False)
            self._set_widget_state(widgets.get("unit_widget"), False)
            self._set_widget_state(widgets.get("to_user_widget"), False)
            self._set_widget_state(widgets.get("to_vault_widget"), False)
            
        elif tx_type_lower == "withdraw":
            # Enable: category, quantity, unit
            # Disable: to_user, to_vault
            self._set_widget_state(widgets.get("category_widget"), True)
            self._set_widget_state(widgets.get("quantity_widget"), True)
            self._set_widget_state(widgets.get("unit_widget"), True)
            self._set_widget_state(widgets.get("to_user_widget"), False)
            self._set_widget_state(widgets.get("to_vault_widget"), False)
            
        elif tx_type_lower == "transfer":
            # Enable: to_user, to_vault
            # Disable: category, quantity, unit
            self._set_widget_state(widgets.get("category_widget"), False)
            self._set_widget_state(widgets.get("quantity_widget"), False)
            self._set_widget_state(widgets.get("unit_widget"), False)
            self._set_widget_state(widgets.get("to_user_widget"), True)
            self._set_widget_state(widgets.get("to_vault_widget"), True)
            
        else:
            # No type selected - disable everything except type
            self._set_widget_state(widgets.get("vault_widget"), False)
            self._set_widget_state(widgets.get("amount_widget"), False)
            self._set_widget_state(widgets.get("category_widget"), False)
            self._set_widget_state(widgets.get("description_widget"), False)
            self._set_widget_state(widgets.get("quantity_widget"), False)
            self._set_widget_state(widgets.get("unit_widget"), False)
            self._set_widget_state(widgets.get("to_user_widget"), False)
            self._set_widget_state(widgets.get("to_vault_widget"), False)
            self._set_widget_state(widgets.get("date_widget"), False)
    
    def _set_widget_state(self, widget, enabled: bool):
        """Enable or disable a widget"""
        if widget is None:
            return
        
        state = "normal" if enabled else "disabled"
        try:
            widget.configure(state=state)
        except:
            pass
    
    def add_row(self):
        """Add a new row to the grid (preserving existing data)"""
        # Store existing data first
        existing_data = [self.get_row_data(i) for i in range(len(self.row_widgets))]
        
        self.row_count += 1
        
        # Rebuild grid
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self._build_header()
        self._build_rows()
        
        # Restore data
        for i, data in enumerate(existing_data):
            if i < len(self.row_widgets):
                self.set_row_data(i, data)
    
    def regenerate_rows(self, new_count: int):
        """Regenerate grid with new row count, preserving existing data"""
        # Store existing data
        existing_data = [self.get_row_data(i) for i in range(len(self.row_widgets))]
        
        self.row_count = new_count
        
        # Clear and rebuild
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self._build_header()
        self._build_rows()
        
        # Restore data (up to min of old/new count)
        for i, data in enumerate(existing_data):
            if i < len(self.row_widgets):
                self.set_row_data(i, data)
    
    def get_row_data(self, row_index: int) -> Dict[str, str]:
        """Get data from a specific row"""
        if row_index >= len(self.row_widgets):
            return {}
        
        widgets = self.row_widgets[row_index]
        data = {}
        
        for key, var in widgets.items():
            if isinstance(var, ctk.StringVar):
                data[key] = var.get()
        
        return data
    
    def set_row_data(self, row_index: int, data: Dict[str, str]):
        """Set data for a specific row"""
        if row_index >= len(self.row_widgets):
            return
        
        widgets = self.row_widgets[row_index]
        
        for key, value in data.items():
            if key in widgets and isinstance(widgets[key], ctk.StringVar):
                widgets[key].set(value)
        
        # Update field states based on type
        tx_type = data.get("type", "")
        if tx_type:
            self._update_field_states(row_index, tx_type)
    
    def get_all_rows(self) -> List[TransactionRow]:
        """Get all rows as TransactionRow objects"""
        rows = []
        
        for i, widgets in enumerate(self.row_widgets):
            data = self.get_row_data(i)
            
            # Parse amount
            amount = None
            if data.get("amount"):
                try:
                    amount = float(data["amount"])
                except ValueError:
                    amount = None
            
            # Parse quantity
            quantity = None
            if data.get("quantity"):
                try:
                    quantity = float(data["quantity"])
                except ValueError:
                    quantity = None
            
            row = TransactionRow(
                row_number=i + 1,
                transaction_type=data.get("type", ""),
                vault=data.get("vault", ""),
                amount=amount,
                category=data.get("category", ""),
                description=data.get("description", ""),
                quantity=quantity,
                unit=data.get("unit", ""),
                to_user=data.get("to_user", ""),
                to_vault=data.get("to_vault", ""),
                date=data.get("date", "")
            )
            
            rows.append(row)
        
        return rows
    
    def clear_all(self):
        """Clear all row data"""
        for i in range(len(self.row_widgets)):
            for key, var in self.row_widgets[i].items():
                if isinstance(var, ctk.StringVar):
                    var.set("")
            # Reset field states
            self._update_field_states(i, "")


class PreviewTable(ctk.CTkFrame):
    """Read-only preview table for transaction confirmation"""
    
    def __init__(self, parent, rows: List[TransactionRow]):
        super().__init__(parent, fg_color=UIConfig.COLOR_FRAME_DARK)
        
        self.rows = [r for r in rows if not r.is_empty()]
        self._build_ui()
    
    def _build_ui(self):
        """Build preview table"""
        if not self.rows:
            label = ctk.CTkLabel(
                self,
                text="No transactions to preview",
                font=UIConfig.FONT_NORMAL
            )
            label.pack(pady=20)
            return
        
        # Summary header
        summary = self._get_summary()
        summary_label = ctk.CTkLabel(
            self,
            text=summary,
            font=UIConfig.FONT_HEADING,
            text_color=UIConfig.COLOR_SUCCESS
        )
        summary_label.pack(pady=10)
        
        # Build table data
        headers = ["#", "Type", "Vault", "Amount", "Details", "Date"]
        table_data = [headers]
        
        for row in self.rows:
            details = self._format_details(row)
            table_data.append([
                str(row.row_number),
                row.transaction_type,
                row.vault,
                f"{row.amount:.2f}" if row.amount else "",
                details,
                row.date or "Now"
            ])
        
        # Create table
        table = CTkTable(
            self,
            values=table_data,
            header_color=UIConfig.COLOR_SECONDARY,
            hover_color=UIConfig.COLOR_FRAME_LIGHT
        )
        table.pack(pady=10, padx=10, fill="both", expand=True)
    
    def _format_details(self, row: TransactionRow) -> str:
        """Format row details for preview"""
        tx_type = row.transaction_type.lower()
        
        if tx_type == "deposit":
            return f"{row.category}: {row.description}"
        elif tx_type == "withdraw":
            qty_str = f"{row.quantity} {row.unit}" if row.quantity else ""
            return f"{row.category}: {row.description} {qty_str}".strip()
        elif tx_type == "transfer":
            return f"To {row.to_user}/{row.to_vault}: {row.description}"
        
        return row.description
    
    def _get_summary(self) -> str:
        """Get summary text"""
        total_count = len(self.rows)
        
        total_deposits = sum(r.amount for r in self.rows 
                           if r.transaction_type.lower() == "deposit" and r.amount)
        total_withdraws = sum(r.amount for r in self.rows 
                            if r.transaction_type.lower() == "withdraw" and r.amount)
        total_transfers = sum(r.amount for r in self.rows 
                            if r.transaction_type.lower() == "transfer" and r.amount)
        
        return (f"Total: {total_count} transactions | "
                f"Deposits: +{total_deposits:.2f} | "
                f"Withdraws: -{total_withdraws:.2f} | "
                f"Transfers: {total_transfers:.2f}")