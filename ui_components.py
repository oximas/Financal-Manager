import customtkinter as ctk
from typing import Any, Callable, List, Optional, Dict, Tuple
from config import UIConfig

class FormField:
    """Represents a form field with label and input"""
    def __init__(
            self,
            parent:ctk.CTkFrame,
            label_text:str,
            row:int,
            field_type: str="entry",
            placeholder:str="",
            show:str="",
            values:Optional[List[str]]= None,
            default_value:str = ""):
        self.label = ctk.CTkLabel(parent, text= label_text)
        self.label.grid(row=row,column=0,sticky="e",padx=10,pady=5)

        if field_type == "entry":
            self.widget = ctk.CTkEntry(parent,placeholder_text=placeholder,show=show)
        elif field_type == "combobox":
            self.variable = ctk.StringVar(parent)
            self.variable.set(default_value)
            self.widget = ctk.CTkComboBox(
                parent,
                variable = self.variable,
                values=values or []
            )
        elif field_type == "date":
            try:
                from CTkDatePicker import CTkDatePicker
                self.widget = CTkDatePicker(parent)
                self.widget.set_date_format("%Y-%m-%d")

            except ModuleNotFoundError:
                print("CTkDatePicker doesnt exist")
        self.widget.grid(row=row,column=1,padx=10,pady=5)
        self.field_type = field_type
    
    def get_value(self)->str:
        """Get the current values of the field"""
        if self.field_type=="combobox":
            return self.variable.get()
        elif self.field_type=="date":
            return self.widget.get_date() if hasattr(self.widget,'get_date') else "" #type:ignore
        else:
            return self.widget.get() #type:ignore
    
    def set_value(self, value:str):
        """Set the value of the field"""
        if self.field_type == "combobox":
            self.variable.set(value)
        elif self.field_type != "date":
            self.widget.delete(0,"end")#type:ignore
            self.widget.insert(0,value)#type:ignore

class FormBuilder:
    """Builder for creating forms with multiple fields"""
    
    def __init__(self, parent:ctk.CTkFrame):
        self.parent = parent
        self.fields:Dict[str,FormField] = {}
        self.current_row = 1

    def add_title(self,text:str) -> 'FormBuilder':
        """Adds title to form"""
        title_label = ctk.CTkLabel(
            self.parent,
            text=text,
            font=UIConfig.FONT_TITLE,
            text_color=UIConfig.COLOR_TEXT_DARK,
            anchor="center"
        )
        title_label.grid(row=0,column=0,columnspan=2,pady=(20,10))
        return self
    def add_field(
            self,
            name: str,
            label:str,
            field_type: str = "entry",
            **kwargs
    ) -> 'FormBuilder':
        """Add a field to the form"""
        field = FormField(
            self.parent,
            label,
            self.current_row,
            field_type,
            **kwargs)
        self.fields[name] = field
        self.current_row +=1
        return self
    def add_button(
        self,
        text: str,
        command: Callable,
        fg_color: Optional[str] = None,
        text_color: Optional[str] = None,
        colspan: int = 2
    ) -> 'FormBuilder':
        """Add a button to the form"""
        button = ctk.CTkButton(
            self.parent,
            text=text,
            command=command,
            fg_color=fg_color or UIConfig.COLOR_PRIMARY,
            text_color=text_color or UIConfig.COLOR_TEXT_DARK,
            font=UIConfig.FONT_BUTTON
        )
        button.grid(
            row=self.current_row,
            column=0,
            columnspan=colspan,
            sticky="ew",
            pady=10
        )
        self.current_row += 1
        return self
    def get_values(self) -> Dict[str, str]:
        """Get all field values as a dictionary"""
        return {name: field.get_value() for name, field in self.fields.items()}
    
    def get_value(self, name: str) -> str:
        """Get a single field value"""
        return self.fields[name].get_value() if name in self.fields else ""

class CenteredForm(ctk.CTkFrame):
    """A centered frame for forms"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configure grid to center the form
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(100, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(2, weight=1)
        
        self.grid(row=1, column=1, sticky="nsew")
    
class MessageHelper:
    """Helper class for showing messages"""
    
    @staticmethod
    def show_error(title: str, message: str):
        """Show an error message"""
        from tkinter import messagebox
        messagebox.showerror(title, message)
    
    @staticmethod
    def show_info(title: str, message: str):
        """Show an info message"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    @staticmethod
    def show_warning(title: str, message: str):
        """Show a warning message"""
        from tkinter import messagebox
        messagebox.showwarning(title, message)

class VaultSummaryCard(ctk.CTkFrame):
    """A card displaying vault information"""

    def __init__(self, parent, vault_name:str, balance:float):
        name_label = ctk.CTkLabel(
            self,
            text=f"{vault_name}:",
            font = UIConfig.FONT_NORMAL,
            text_color=UIConfig.COLOR_TEXT_PRIMARY
        )

        name_label.pack(side="left",padx=10, pady=5)

        balance_label = ctk.CTkLabel(
            self,
            text=f"{balance:.2f} EGP", #<-- abstract this away into a "currency" variable
            font=UIConfig.FONT_NORMAL,
            text_color=UIConfig.COLOR_TEXT_SECONDARY,
        )
        balance_label.pack(side="right", padx=10, pady=5)

class MenuButton(ctk.CTkButton):
    """Styled button for menu navigation"""

    def __init__(
            self,
            parent,
            text:str,
            command: Callable,
            button_type: str = "primary"
    ):
        colors = {
            "primary": (UIConfig.COLOR_PRIMARY,UIConfig.COLOR_TEXT_DARK),
            "secondary": (UIConfig.COLOR_SECONDARY,UIConfig.COLOR_TEXT_PRIMARY),
            "back": (UIConfig.COLOR_SECONDARY,UIConfig.COLOR_TEXT_PRIMARY),
        }
        fg_color, text_color = colors.get(button_type,colors["primary"])

        super().__init__(
            parent,
            text=text,
            command=command,
            fg_color=fg_color,
            text_color=text_color,
            width=UIConfig.BUTTON_WIDTH,
            font=UIConfig.FONT_BUTTON
        )
