import tkinter as tk
import customtkinter as ctk 
from customtkinter import * # type: ignore
from CTkDatePicker import CTkDatePicker
from datetime import datetime
from tkinter import * # type: ignore
from tkinter import messagebox
from Database import Database as DB
set_appearance_mode("System")
set_default_color_theme('blue')

# GUI Interface
class GUI:
    def run(self):
        self.db = DB("personal_financial_manager.db")

        self.master = CTk()
        self.master.title("Finance Manager")
        self.default_width = 400
        self.default_height = 300
        self.master.geometry(f"{self.default_width}x{self.default_height}")
        self.master.configure(fg_color="#000000")

        #zoom variables 
        self.zoom_level = 1.0  # Default zoom (100%)
        self.min_zoom = 0.8    # 80% minimum zoom
        self.max_zoom = 2.0    # 200% maximum zoom
        self.master.bind("<Control-MouseWheel>", self.zoom_handler)  # Windows/Linux
        self.master.bind("<Control-Button-4>", self.zoom_handler)    # Mac (up)
        self.master.bind("<Control-Button-5>", self.zoom_handler)    # Mac (down)
        # Store widgets that need zooming
        self.zoomable_widgets = {}
        self.main_menu()  # Calls the menu with login/signup options

        ## For debuging certain menus uncoment the code below
        ## and call self."name of menu"
        #self.username="Home"
        #self.transaction_menu("Withdraw")

    def main_menu(self):
        self.destroy_all_widgets()
        self.master.title("Finance Manager - Welcome")

        self.login_button = CTkButton(self.master, text="Login", command=self.login_menu, width=200)
        self.login_button.pack(pady=10)

        self.signup_button = CTkButton(self.master, text="Sign Up", command=self.signup_menu, width=200)
        self.signup_button.pack(pady=10)

        self.window_resize()
    def login_menu(self):
        self.destroy_all_widgets()
        self.master.title("Login")

        # Username
        self.username_label = CTkLabel(self.master, text="Username:", text_color="white")
        self.username_label.pack(pady=2)

        self.username_entry = CTkEntry(self.master, placeholder_text="Enter username", width=250)
        self.username_entry.pack(pady=5)

        # Password
        self.password_label = CTkLabel(self.master, text="Password:", text_color="white")
        self.password_label.pack(pady=2)

        self.password_entry = CTkEntry(self.master, placeholder_text="Enter password", show="*", width=250)
        self.password_entry.pack(pady=5)

        # Buttons
        self.login_button = CTkButton(self.master, text="Login", command=lambda: self.login(
            self.username_entry.get(), self.password_entry.get()), fg_color="#98FB98", text_color="black", width=200)
        self.login_button.pack(pady=10)

        self.back_button = CTkButton(self.master, text="Back", command=self.main_menu, fg_color="#444", width=200)
        self.back_button.pack(pady=5)

        self.window_resize()

    def signup_menu(self):
        self.destroy_all_widgets()
        self.master.title("Sign Up")

        # Username
        self.username_label = CTkLabel(self.master, text="Username:", text_color="white")
        self.username_label.pack(pady=2)

        self.username_entry = CTkEntry(self.master, placeholder_text="Enter username", width=250)
        self.username_entry.pack(pady=5)

        # Password
        self.password_label = CTkLabel(self.master, text="Password:", text_color="white")
        self.password_label.pack(pady=2)

        self.password_entry = CTkEntry(self.master, placeholder_text="Enter password", show="*", width=250)
        self.password_entry.pack(pady=5)

        # Confirm Password
        self.confirm_password_label = CTkLabel(self.master, text="Confirm Password:", text_color="white")
        self.confirm_password_label.pack(pady=2)

        self.confirm_password_entry = CTkEntry(self.master, placeholder_text="Confirm password", show="*", width=250)
        self.confirm_password_entry.pack(pady=5)

        # Sign Up Button
        self.signup_button = CTkButton(self.master, text="Sign Up", command=lambda: self.signup(
            self.username_entry.get(), self.password_entry.get(), self.confirm_password_entry.get()), 
            fg_color="#98FB98", text_color="black", width=200)
        self.signup_button.pack(pady=10)

        # Back Button
        self.back_button = CTkButton(self.master, text="Back", command=self.main_menu, fg_color="#444", width=200)
        self.back_button.pack(pady=5)

        self.window_resize()
    def login(self,username,password):
        correct_password = self.db.check_user_password(username,password)
        if correct_password:
            self.username=username.capitalize()
            self.user_menu()
        else:
            messagebox.showerror("Incorect login info","your username and password don't match")

    def signup(self,username,password,check_password):
        if(password!=check_password):
            messagebox.showerror("password error","both passwords must match")
            return
        if(self.db.user_exists(username)):
             messagebox.showerror("dublicate username","username already exists")
             return
        self.db.add_user(username,password)
        self.username=username.capitalize()
        self.user_menu()

    def user_menu(self):
        self.destroy_all_widgets()

        self.master.title(f"Finance Manager - {self.username.capitalize()}")  # Show the username in the title

        self.deposit_button = CTkButton(self.master, text="Deposit", command=self.deposit_menu)
        self.deposit_button.pack(pady=2)

        self.withdraw_button = CTkButton(self.master, text="Withdraw", command=self.withdraw_menu)
        self.withdraw_button.pack(pady=2)

        self.transfer_button = CTkButton(self.master, text="Transfer", command=self.transfer_menu)
        self.transfer_button.pack(pady=2)


        self.summary_button = CTkButton(self.master, text="Summary", command=self.summary_menu)
        self.summary_button.pack(pady=2)

        self.account_button = CTkButton(self.master, text="Account", command=self.account_menu)
        self.account_button.pack(pady=2)
        
        self.window_resize()

    def deposit_menu(self):
        self.transaction_menu("Deposit")

    def withdraw_menu(self):
        self.transaction_menu("Withdraw")

    def transaction_menu(self, transaction_type):
        self.destroy_all_widgets()

        # Configure rows and columns to expand
        self.master.grid_rowconfigure(0, weight=1)  # Add weight to the top row
        self.master.grid_rowconfigure(100, weight=1)  # Add weight to the bottom row
        self.master.grid_columnconfigure(0, weight=1)  # Add weight to the left column
        self.master.grid_columnconfigure(2, weight=1)  # Add weight to the right column

        # Create a central frame to hold all widgets
        central_frame = CTkFrame(self.master)
        central_frame.grid(row=1, column=1, sticky="nsew")  # Center the frame

        # Add a title label inside the central frame
        title_label = CTkLabel(
            central_frame,
            text=f"{transaction_type} Menu",
            font=("Arial", 24, "bold"),  # Larger font size and bold style
            text_color="#111",  # Dark gray color for contrast
            anchor="center"  # Center-align the text
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))  # Add padding for spacing

        # Row index for grid placement inside the central frame
        row_index = 1  # Start below the title

        # Money Amount
        amount_label = CTkLabel(central_frame, text="Money Amount:")
        amount_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=5)
        amount_entry = CTkEntry(central_frame)
        amount_entry.grid(row=row_index, column=1, padx=10, pady=5)
        row_index += 1

        # Category
        category_label = CTkLabel(central_frame, text="Category:")
        category_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=5)
        category_names = self.db.get_category_names()
        chosen_category = StringVar(central_frame)
        chosen_category.set(category_names[0] if len(category_names) else "Please add more categories")
        category_options = CTkComboBox(central_frame, variable=chosen_category, values=category_names)
        category_options.grid(row=row_index, column=1, padx=10, pady=5)
        row_index += 1

        # Description
        description_label = CTkLabel(central_frame, text="Description:")
        description_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=5)
        description_entry = CTkEntry(central_frame)
        description_entry.grid(row=row_index, column=1, padx=10, pady=5)
        row_index += 1

        # Withdraw-specific fields
        if transaction_type == "Withdraw":
            # Quantity
            quantity_label = CTkLabel(central_frame, text="Quantity:")
            quantity_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=5)
            quantity_entry = CTkEntry(central_frame)
            quantity_entry.grid(row=row_index, column=1, padx=10, pady=5)
            row_index += 1

            # Unit
            unit_label = CTkLabel(central_frame, text="Unit:")
            unit_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=5)
            unit_names = self.db.get_unit_names()
            chosen_unit = StringVar(central_frame)
            chosen_unit.set(unit_names[0] if len(unit_names) else "Please add more units")
            unit_options = CTkComboBox(central_frame, variable=chosen_unit, values=unit_names)
            unit_options.grid(row=row_index, column=1, padx=10, pady=5)
            row_index += 1

        # Vault
        vault_label = CTkLabel(central_frame, text="Vault:")
        vault_label.grid(row=row_index, column=0, sticky="e", padx=10, pady=5)
        chosen_vault = StringVar(central_frame)
        chosen_vault.set("Main")
        vault_options = CTkComboBox(central_frame, variable=chosen_vault, values=self.db.get_user_vault_names(self.username))
        vault_options.grid(row=row_index, column=1, padx=10, pady=5)
        row_index += 1

        date_label = CTkLabel(central_frame,text="Date:")
        date_label.grid(row=row_index,column=0,sticky="e",padx=10,pady=5)
        date_picker = CTkDatePicker(central_frame)
        date_picker.set_date_format("%Y-%m-%d")
        date_picker.grid(row = row_index,column = 1,padx=10,pady=5)
        row_index+=1
        
        # Submit Button (Stretched Across Screen)
        def date_get():
            return date_picker.get_date() + " " + datetime.now().strftime("%H:%M:%S") if date_picker.get_date() else None
        if transaction_type == "Withdraw":
            submit_button = CTkButton(
                central_frame,
                text=transaction_type,
                fg_color="#98FB98",
                text_color="black",
                command=lambda: self.process_transaction(
                    transaction_type,
                    chosen_vault.get(),
                    amount_entry.get(),
                    chosen_category.get(),
                    description_entry.get(),
                    quantity_entry.get(),
                    chosen_unit.get(),
                    date= date_get()
                )
            )
        elif transaction_type == "Deposit":
            submit_button = CTkButton(
                central_frame,
                text=transaction_type,
                fg_color="#98FB98",
                text_color="black",
                command=lambda: self.process_transaction(
                    transaction_type,
                    chosen_vault.get(),
                    amount_entry.get(),
                    chosen_category.get(),
                    description_entry.get(),
                    date= date_get()
                )
            )
        else:
            raise ValueError("Transaction type must be 'Withdraw' or 'Deposit'")
        
        submit_button.grid(row=row_index, column=0, columnspan=2, sticky="ew", pady=10)
        row_index += 1
        
        # Back Button (Stretched Across Screen)
        back_button = CTkButton(
            central_frame,
            text="Back",
            fg_color="#444",
            text_color="white",
            command=lambda: self.user_menu()
        )
        back_button.grid(row=row_index, column=0, columnspan=2, sticky="ew", pady=5)

        # Resize window
        self.window_resize()
        for widget in self.master.winfo_children():
            self.zoomable_widgets[f"{widget}"] = widget


    def process_transaction(self, transaction_type,vault,money_amount,category_name,description,quantity=None,unit=None,date=None):
        try:
            if(transaction_type=="Withdraw"):
                self.db.withdraw(self.username,vault,money_amount,category_name,description,quantity,unit,date)
                print("Withdrew")
            elif(transaction_type=="Deposit"):
                self.db.deposit(self.username,vault,money_amount,category_name,description,quantity,unit,date)
                print("Depsited")
            else:
                raise ValueError("transaction type must be 'Withdraw' or 'Deposit' ")
        except:
            messagebox.showerror("Unsuccessful Transaction",f"{transaction_type} transaction was unsuccessful")
        else:
            messagebox.showinfo("Successful Transaction",f"{transaction_type} trans was successful")
        

    def transfer_menu(self):
        self.destroy_all_widgets()
        self.master.title("Transfer Menu")

        # Configure rows and columns to expand
        self.master.grid_rowconfigure(0, weight=1)  # Add weight to the top row
        self.master.grid_rowconfigure(100, weight=1)  # Add weight to the bottom row
        self.master.grid_columnconfigure(0, weight=1)  # Add weight to the left column
        self.master.grid_columnconfigure(2, weight=1)  # Add weight to the right column

        # Create a central frame to hold all widgets
        central_frame = ctk.CTkFrame(self.master)
        central_frame.grid(row=1, column=1, sticky="nsew")  # Center the frame

        # Add a title label inside the central frame
        title_label = ctk.CTkLabel(
            central_frame,
            text="Transfer Menu",
            font=("Arial", 24, "bold"),
            text_color="#111",  # Dark gray color for contrast
            anchor="center"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))  # Add padding for spacing

        # Row index for grid placement inside the central frame
        row_index = 1  # Start below the title

        # Fetch vaults for current user
        from_vault_names = self.db.get_user_vault_names(self.username)

        # "From" Vault Selection
        from_vault_label = ctk.CTkLabel(central_frame, text="From:", text_color="white")
        from_vault_label.grid(row=row_index, column=0, padx=5, pady=5, sticky="e")

        from_vault = StringVar(central_frame)
        from_vault.set(from_vault_names[0] if from_vault_names else "No Vaults Available")
        from_vault_options = ctk.CTkComboBox(central_frame, variable=from_vault, values=from_vault_names)
        from_vault_options.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
        row_index += 1

        # "To User" Selection
        to_user_label = ctk.CTkLabel(central_frame, text="To User:", text_color="white")
        to_user_label.grid(row=row_index, column=0, padx=5, pady=5, sticky="e")

        to_user = StringVar(central_frame)
        to_user.set(self.username)
        to_user_options = ctk.CTkComboBox(
            central_frame,
            variable=to_user,
            values=self.db.get_usernames(),
            command=lambda username: refresh_to_user_vault_names(username)
        )
        to_user_options.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
        row_index += 1

        # Fetch vaults for selected user
        to_vault_names = self.db.get_user_vault_names(to_user.get())

        # "To Vault" Selection
        to_vault_label = ctk.CTkLabel(central_frame, text="To Vault:", text_color="white")
        to_vault_label.grid(row=row_index, column=0, padx=5, pady=5, sticky="e")

        to_vault = StringVar(central_frame)
        to_vault.set(to_vault_names[0] if to_vault_names else "No Vaults Available")
        to_vault_options = ctk.CTkComboBox(central_frame, variable=to_vault, values=to_vault_names)
        to_vault_options.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
        row_index += 1

        # "Amount" Entry
        amount_label = ctk.CTkLabel(central_frame, text="Amount:", text_color="white")
        amount_label.grid(row=row_index, column=0, padx=5, pady=5, sticky="e")

        amount_entry = ctk.CTkEntry(central_frame, placeholder_text="Enter amount")
        amount_entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
        row_index += 1

        # "Reason" Entry
        reason_label = ctk.CTkLabel(central_frame, text="Reason (optional):", text_color="white")
        reason_label.grid(row=row_index, column=0, padx=5, pady=5, sticky="e")

        reason_entry = ctk.CTkEntry(central_frame, placeholder_text="Enter reason (optional)")
        reason_entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
        row_index += 1

        # "Transfer" Button
        submit_button = ctk.CTkButton(
            central_frame,
            text="Transfer",
            fg_color="#98FB98",
            text_color="black",
            command=lambda: self.process_transfer(
                from_vault.get(), to_user.get(), to_vault.get(),
                amount_entry.get(), reason_entry.get()
            )
        )
        submit_button.grid(row=row_index, column=0, columnspan=2, pady=10, sticky="ew")
        row_index += 1

        # "Back" Button
        back_button = ctk.CTkButton(
            central_frame,
            text="Back",
            fg_color="#444",
            text_color="white",
            command=self.user_menu
        )
        back_button.grid(row=row_index, column=0, columnspan=2, pady=5, sticky="ew")

        # Resize window
        self.window_resize()

        def refresh_to_user_vault_names(username):
            """ Refresh the vault options for the selected recipient user. """
            to_vault_names = self.db.get_user_vault_names(username)

            # Ensure there are available vaults
            if to_vault_names:
                to_vault.set(to_vault_names[0])  # Set default value
                to_vault_options.configure(values=to_vault_names)  # Update dropdown options
            else:
                to_vault.set("No Vaults Available")  # Set default value if empty
                to_vault_options.configure(values=["No Vaults Available"])

        def refresh_from_user_vault_names(username):
            """ Refresh the vault options for the sender user. """
            from_vault_names = self.db.get_user_vault_names(username)

            # Ensure there are available vaults
            if from_vault_names:
                from_vault.set(from_vault_names[0])  # Set default value
                from_vault_options.configure(values=from_vault_names)  # Update dropdown options
            else:
                from_vault.set("No Vaults Available")  # Set default value if empty
                from_vault_options.configure(values=["No Vaults Available"])




    def process_transfer(self,from_vault,to_user,to_vault,amount,reason):
        try:
            if(float(amount)<=0):
                messagebox.showwarning("incorrect money amount","amount must be a postive number")
                return
            if(self.username==to_user and from_vault==to_vault):
                messagebox.showwarning("incorrect transaction","cannot transfer to the same vault that you are taking money out of")
            self.db.transfer(self.username,from_vault,to_user,to_vault,amount,reason)
        except:
            messagebox.showerror("Unsuccessful Transaction","Transfer interaction was unsuccessful")
        else:
            messagebox.showinfo("Successful Transaction","Transfer interaction was successful")



    

    def refresh_to_user_vault_names(self, username):
        """ Refresh the vault options for the selected recipient user. """
        to_vault_names = self.db.get_user_vault_names(username)
        if to_vault_names:
            self.to_vault.set(to_vault_names[0])  # Set first vault as default
            self.to_vault_options.configure(values=to_vault_names)  # Update dropdown
        else:
            self.to_vault.set("No Vaults")  # Set fallback value
            self.to_vault_options.configure(values=["No Vaults"])

    def refresh_from_user_vault_names(self, username):
        """ Refresh the vault options for the selected sender user. """
        from_vault_names = self.db.get_user_vault_names(username)
        if from_vault_names:
            self.from_vault.set(from_vault_names[0])  # Set first vault as default
            self.from_vault_options.configure(values=from_vault_names)  # Update dropdown
        else:
            self.from_vault.set("No Vaults")  # Set fallback value
            self.from_vault_options.configure(values=["No Vaults"])


    
        

    
    def summary_menu(self):
        self.destroy_all_widgets()

        self.master.title("Summary Menu")
        
        # Main container frame with sleek design
        container = CTkFrame(self.master, corner_radius=15, fg_color="#222")
        container.pack(pady=20, padx=30, fill='both', expand=True)
        
        # Total Balance Label with a modern font
        self.total_label = CTkLabel(container, text=f"Total Amount: {self.db.get_user_balance(self.username):.2f} EGP", 
                                    font=("Helvetica", 18, "bold"), text_color="#00FFC6")
        self.total_label.pack(pady=15)
        
        # Vault Details Section
        vault_frame = CTkFrame(container, corner_radius=10, fg_color="#333")
        vault_frame.pack(pady=10, padx=10, fill='x')
        CTkLabel(vault_frame, text="Vault Details:", font=("Helvetica", 16, "bold"), text_color="#FFFFFF").pack(pady=5)
        vaults = self.db.get_user_vaults(self.username)
        for vault_name, balance in vaults.items():
            CTkLabel(vault_frame, text=f"{vault_name}: {balance:.2f} EGP", text_color="#BBBBBB").pack(pady=3)
        
               
        # Back Button with a sleek look
        self.back_button = CTkButton(container, text="Back", fg_color="#00FFC6", text_color="#111", 
                                    font=("Helvetica", 14, "bold"), corner_radius=12, command=lambda: self.user_menu())
        self.back_button.pack(pady=20)
        
        self.window_resize()


    def account_menu(self):
        self.destroy_all_widgets()

        self.username_label = CTkLabel(self.master,text=f"Username: {self.username}")
        self.username_label.pack(pady=2)

        self.add_vault_button = CTkButton(self.master,text="Add vault",fg_color="#444", text_color="white", command = self.add_vault)
        self.add_vault_button.pack(pady=2)

        self.change_password_button = CTkButton(self.master,fg_color="#444", text_color="white",text="Change password")
        self.change_password_button.pack(pady=2)

        self.export_button = CTkButton(self.master, text="Export data to Excel",fg_color="#444", text_color="white", command=self.export_to_excel)
        self.export_button.pack(pady=10)
        
        self.logout_button = CTkButton(self.master, fg_color="#98FB98", text_color="black", text="Logout", command=self.main_menu)
        self.logout_button.pack(pady=2)

        self.back_button = CTkButton(self.master, text="Back" ,fg_color="#444", text_color="white", command=self.user_menu)
        self.back_button.pack(pady=2)

        self.window_resize()
    def add_vault(self):
        pass
        ask_new_name = CTkInputDialog(text="New vault name is:", title="Add new vault")
        new_vault_name = ask_new_name.get_input()
        new_vault_name=new_vault_name.capitalize()
        if new_vault_name:
            try:
                self.db.add_vault(self.username,new_vault_name)
            except:
                messagebox.showerror("Failed to add new vault", f"Vault '{new_vault_name}' already exists in your vaults!")
            else:
                messagebox.showinfo("Success", f"Vault '{new_vault_name}' added successfully!")

        elif new_vault_name=="":
            messagebox.showerror("Error", "Vault name can't be empty")
            
    def export_to_excel(self):
        # Replace with actual functionality
        print("Export to Excel called")
        try:
            self.db.export_to_excel(self.username)
        except PermissionError:
            messagebox.showerror("couldn't export into excel",'''close any instancesof the file, 
                                                                and make sure you have write permissions''')
         
    def destroy_all_widgets(self):
         for widget in self.master.winfo_children():
            widget.destroy()
    def window_resize(self):
        self.master.update_idletasks()
        width = self.master.winfo_reqwidth()
        height = self.master.winfo_reqheight()
        margin = 20
        self.master.geometry(f"{max(width+margin,self.default_width)}x{max(height+margin,self.default_height)}")

    def zoom_handler(self, event):
        # Determine zoom direction (1 for up, -1 for down)
        delta = 1 if (event.delta > 0 or event.num == 4) else -1
        
        # Calculate new zoom level (with constraints)
        new_zoom = self.zoom_level + (delta * 0.1)  # 10% per step
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self.apply_zoom()

    def apply_zoom(self):
        """Applies zoom level to all tracked widgets"""
        try:
            for widget_name, widget in self.zoomable_widgets.items():
                # Skip if widget is destroyed or not available
                if not widget.winfo_exists():
                    continue

                # 1. FONT SCALING
                if hasattr(widget, 'configure') and 'font' in widget.configure():
                    current_font = widget.cget('font')
                    
                    # Handle different font formats
                    if isinstance(current_font, (tuple, list)):
                        # Case 1: ('Arial', 12) or ('Arial', 12, 'bold')
                        font_parts = list(current_font)
                        if len(font_parts) >= 2 and isinstance(font_parts[1], (int, float)):
                            font_parts[1] = int(font_parts[1] * self.zoom_level)
                            widget.configure(font=tuple(font_parts))
                    elif isinstance(current_font, str):
                        # Case 2: "Arial 12 bold" (less common in CTkinter)
                        pass  # Add string parsing if needed

                # 2. WIDGET DIMENSIONS
                for dimension in ['height', 'width']:
                    if hasattr(widget, 'configure') and dimension in widget.configure():
                        current_val = widget.cget(dimension)
                        if isinstance(current_val, (int, float)):
                            widget.configure(**{dimension: int(current_val * self.zoom_level)})

                # 3. SPECIAL CASES
                if isinstance(widget, ctk.CTkFrame):
                    # Scale internal padding for frames
                    for child in widget.winfo_children():
                        child.grid_configure(
                            padx=int(10 * self.zoom_level),
                            pady=int(5 * self.zoom_level)
                        )
                
                

        except Exception as e:
            print(f"Zoom error on {widget_name}: {str(e)}")
                    
# Main Application
root = CTk()
app = GUI(root)
root.mainloop()

