import tkinter as tk
import customtkinter as ctk
from customtkinter import *
from tkinter import * # type: ignore
from tkinter import messagebox
from Database import Database as DB
set_appearance_mode("System")
set_default_color_theme('blue')

# GUI Interface
class GUI:
    def __init__(self, master):

        self.db = DB("personal_financial_manager.db")

        self.master = master
        self.master.title("Finance Manager")
        self.default_width = 400
        self.default_height = 300
        self.master.geometry(f"{self.default_width}x{self.default_height}")
        self.master.configure(fg_color="#000000") 

        self.main_menu()  # Calls the menu with login/signup options

    def main_menu(self):
        self.destory_all_widgets()
        self.master.title("Finance Manager - Welcome")

        self.login_button = CTkButton(self.master, text="Login", command=self.login_menu, width=200)
        self.login_button.pack(pady=10)

        self.signup_button = CTkButton(self.master, text="Sign Up", command=self.signup_menu, width=200)
        self.signup_button.pack(pady=10)

        self.window_resize()
    def login_menu(self):
        self.destory_all_widgets()
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
        self.destory_all_widgets()
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
        self.destory_all_widgets()

        self.master.title(f"Finance Manager - {self.username.capitalize()}")  # Show the username in the title

        self.deposit_button = CTkButton(self.master, text="Deposit", command=self.deposit_menu)
        self.deposit_button.pack(pady=2)

        self.withdraw_button = CTkButton(self.master, text="Withdraw", command=self.withdraw_menu)
        self.withdraw_button.pack(pady=2)

        self.transfer_button = CTkButton(self.master, text="Transfer", command=self.transfer_menu)
        self.transfer_button.pack(pady=2)

        self.loan_button = CTkButton(self.master, text="Loan", command=self.loan_menu)
        self.loan_button.pack(pady=2)

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
        self.destory_all_widgets()

        self.master.title(f"{transaction_type} Menu")

        self.amount_label = CTkLabel(self.master, text="Money Amount:")
        self.amount_label.pack(pady=2)
        self.amount_entry = CTkEntry(self.master)
        self.amount_entry.pack(pady=2)

        self.category_label = CTkLabel(self.master, text="Category:")
        self.category_label.pack()
        category_names = self.db.get_category_names()
        #category_names = [name for name in category_names if isinstance(name, str) and name != "Others"]

        chosen_category = StringVar(self.master)
        chosen_category.set(category_names[0] if len(category_names) else "Please add more categories")
        self.category_options = CTkComboBox(self.master,variable=chosen_category, values=category_names)
        self.category_options.pack()

        self.description_label = CTkLabel(self.master, text="Description:")
        self.description_label.pack(pady=2)
        self.description_entry = CTkEntry(self.master)
        self.description_entry.pack(pady=2)

        if(transaction_type=="Withdraw"):
            self.quantity_label = CTkLabel(self.master, text="Quantity:")
            self.quantity_label.pack(pady=2)
            self.quantity_entry = CTkEntry(self.master)
            self.quantity_entry.pack(pady=2)

            self.unit_label = CTkLabel(self.master, text="Unit:")
            self.unit_label.pack()
            unit_names = self.db.get_unit_names()
            chosen_unit = StringVar(self.master)
            chosen_unit.set(unit_names[0] if len(unit_names) else "Please add more units")
            self.unit_options = CTkComboBox(self.master, variable=chosen_unit, values=unit_names)
            self.unit_options.pack()

        self.vault_label = CTkLabel(self.master, text="Vault:")
        self.vault_label.pack()
        chosen_vault = StringVar(self.master)
        chosen_vault.set("Main")
        self.vault_options = CTkComboBox(self.master, variable=chosen_vault, values=self.db.get_user_vault_names(self.username))
        self.vault_options.pack(pady=2)

        if(transaction_type=="Withdraw"):
            self.submit_button = CTkButton(self.master, text=transaction_type, fg_color="#98FB98", text_color="black", 
                                            command=lambda: self.process_transaction(transaction_type, chosen_vault.get(),
                                                                                    self.amount_entry.get(), chosen_category.get(),
                                                                                    self.description_entry.get(), self.quantity_entry.get(),
                                                                                    chosen_unit.get()))
        elif transaction_type=="Deposit":
            self.submit_button = CTkButton(self.master, text=transaction_type,  fg_color="#98FB98", text_color="black",
                                            command=lambda: self.process_transaction(transaction_type, chosen_vault.get(),
                                                                                    self.amount_entry.get(), chosen_category.get(),
                                                                                    self.description_entry.get()))
        else:
            raise ValueError("transaction type must be 'Withdraw' or 'Deposit' ")

        self.submit_button.pack(pady=10)

        self.back_button = CTkButton(self.master, text="Back",fg_color="#444", text_color="white", command=lambda: self.user_menu())
        self.back_button.pack(pady=2)

        self.window_resize()


    def process_transaction(self, transaction_type,vault,money_amount,category_name,description,quantity=None,unit=None):
       
        try:
            if(transaction_type=="Withdraw"):
                self.db.withdraw(self.username,vault,money_amount,category_name,description,quantity,unit)
                print("Withdrew")
            elif(transaction_type=="Deposit"):
                self.db.deposit(self.username,vault,money_amount,category_name,description,quantity,unit)
                print("Depsited")
            else:
                raise ValueError("transaction type must be 'Withdraw' or 'Deposit' ")
        except:
            messagebox.showerror("Unsuccessful Transaction",f"{transaction_type} transaction was unsuccessful")
        else:
            messagebox.showinfo("Successful Transaction",f"{transaction_type} trans was successful")
        

    def transfer_menu(self):
        self.destory_all_widgets()
        self.master.title("Transfer Menu")

        # Fetch vaults for current user
        from_vault_names = self.db.get_user_vault_names(self.username)

        # "From" Vault Selection
        self.from_vault_label = ctk.CTkLabel(self.master, text="From:", text_color="white")
        self.from_vault_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        from_vault = StringVar(self.master)
        from_vault.set(from_vault_names[0])
        self.from_vault_options = ctk.CTkComboBox(self.master, variable=from_vault, values=from_vault_names)
        self.from_vault_options.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # "To User" Selection
        self.to_user_label = ctk.CTkLabel(self.master, text="To user:", text_color="white")
        self.to_user_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        to_user = StringVar(self.master)
        to_user.set(self.username)
        self.to_user_options = ctk.CTkComboBox(
            self.master, variable=to_user, values=self.db.get_usernames(),
            command=lambda username: refresh_to_user_vault_names(username)
        )
        self.to_user_options.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Fetch vaults for selected user
        to_vault_names = self.db.get_user_vault_names(to_user.get())

        # "To Vault" Selection
        self.to_vault_label = ctk.CTkLabel(self.master, text="To vault:", text_color="white")
        self.to_vault_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        to_vault = StringVar(self.master)
        to_vault.set(to_vault_names[0])
        self.to_vault_options = ctk.CTkComboBox(self.master, variable=to_vault, values=to_vault_names)
        self.to_vault_options.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # "Amount" Entry
        self.amount_label = ctk.CTkLabel(self.master, text="Amount:", text_color="white")
        self.amount_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        self.amount_entry = ctk.CTkEntry(self.master, placeholder_text="Enter amount")
        self.amount_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # "Reason" Entry
        self.reason_label = ctk.CTkLabel(self.master, text="Reason (optional):", text_color="white")
        self.reason_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        self.reason_entry = ctk.CTkEntry(self.master, placeholder_text="Enter reason (optional)")
        self.reason_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # "Transfer" Button
        self.submit_button = ctk.CTkButton(
            self.master, text="Transfer", fg_color="#98FB98", text_color="black",
            command=lambda: self.process_transfer(
                from_vault.get(), to_user.get(), to_vault.get(),
                self.amount_entry.get(), self.reason_entry.get()
            )
        )
        self.submit_button.grid(row=5, column=1, padx=5, pady=10, sticky="ew")

        # "Back" Button
        self.back_button = ctk.CTkButton(
            self.master, text="Back", fg_color="#444", text_color="white", command=self.user_menu
        )
        self.back_button.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        self.window_resize()

        def refresh_to_user_vault_names(username):
            """ Refresh the vault options for the selected recipient user. """
            to_vault_names = self.db.get_user_vault_names(username)
            
            # Ensure there are available vaults
            if to_vault_names:
                to_vault.set(to_vault_names[0])  # Set default value
                self.to_vault_options.configure(values=to_vault_names)  # type: ignore # Update dropdown options
            else:
                to_vault.set("No Vaults")  # Set default value if empty
                self.to_vault_options.configure(values=["No Vaults Available"])# type: ignore

        def refresh_from_user_vault_names(username):
            """ Refresh the vault options for the sender user. """
            from_vault_names = self.db.get_user_vault_names(username)
            
            # Ensure there are available vaults
            if from_vault_names:
                from_vault.set(from_vault_names[0])  # Set default value
                self.from_vault_options.configure(values=from_vault_names)  # Update dropdown options # type: ignore
            else:
                from_vault.set("No Vaults")  # Set default value if empty
                self.from_vault_options.configure(values=["No Vaults Available"])# type: ignore




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



    def loan_menu(self):
        self.destory_all_widgets()

        self.master.title("Loan Menu")

        vault_names = self.db.get_user_vault_names(self.username)
        usernames = self.db.get_usernames()

        self.from_user_label = CTkLabel(self.master, text="From user:")
        self.from_user_label.grid(row=0, column=0, padx=5)
        
        self.from_user = StringVar(self.master)
        self.from_user.set(self.username)
        self.from_user_options =CTkComboBox(self.master, variable=self.from_user, values=usernames, 
                                            command=self.refresh_from_user_vault_names)
        self.from_user_options.grid(row=0, column=1)

        from_vault_names = self.db.get_user_vault_names(self.from_user.get())
        self.from_vault_label = CTkLabel(self.master, text="From vault:")
        self.from_vault_label.grid(row=1, column=0, padx=5)
        
        self.from_vault = StringVar(self.master)
        self.from_vault.set(from_vault_names[0] if from_vault_names else "No Vaults")
        self.from_vault_options = CTkComboBox(self.master, variable=self.from_vault, values=from_vault_names or ["No Vaults"])
        self.from_vault_options.grid(row=1, column=1)

        self.to_user_label = CTkLabel(self.master, text="To user:")
        self.to_user_label.grid(row=3, column=0, padx=5)
        
        self.to_user = StringVar(self.master)
        self.to_user.set(self.username)
        self.to_user_options = CTkComboBox(self.master, variable=self.to_user, values=usernames, 
                                            command=self.refresh_to_user_vault_names)
        self.to_user_options.grid(row=3, column=1)

        to_vault_names = self.db.get_user_vault_names(self.to_user.get())
        self.to_vault_label = CTkLabel(self.master, text="To vault:")
        self.to_vault_label.grid(row=4, column=0, padx=5)
        
        self.to_vault = StringVar(self.master)
        self.to_vault.set(to_vault_names[0] if to_vault_names else "No Vaults")
        self.to_vault_options = CTkComboBox(self.master, variable=self.to_vault, values=to_vault_names or ["No Vaults"])
        self.to_vault_options.grid(row=4, column=1)

        self.amount_label = CTkLabel(self.master, text="Amount:")
        self.amount_label.grid(row=5, column=0, pady=2)
        self.amount_entry = CTkEntry(self.master,placeholder_text="Enter amount")
        self.amount_entry.grid(row=5, column=1, pady=2, padx=3)

        self.reason_label = CTkLabel(self.master, text="Reason (not required):")
        self.reason_label.grid(row=6, column=0, pady=2)
        self.reason_entry = CTkEntry(self.master,placeholder_text="Enter reason (optional)")
        self.reason_entry.grid(row=6, column=1, pady=2)

        self.submit_button = CTkButton(self.master, text="Loan",  fg_color="#98FB98", text_color="black",
                                    command=lambda: self.process_loan(
                                        self.from_user.get(), self.from_vault.get(), 
                                        self.to_user.get(), self.to_vault.get(),
                                        self.amount_entry.get(), self.reason_entry.get()
                                    ))
        self.submit_button.grid(row=7, column=1, pady=10)

        self.back_button = CTkButton(self.master, text="Back",fg_color="#444", text_color="white", command=lambda: self.user_menu())
        self.back_button.grid(row=8, column=1, pady=2)

        self.window_resize()

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

    def process_loan(self,from_user,from_vault,to_user,to_vault,amount,reason=None):
        #Feature needed: if from user is not me probably adding a password check would be valid
        #afer that showing the user the ammount of money available then confirming the transaction
        try:
            if(from_user!=self.username and to_user!=self.username):
                messagebox.showwarning("invalid users", "One of the users has to be you!!")
                return
            if(from_user==to_user): # they both would equal to me if thats the case
                messagebox.showwarning("Invalid Users", "Can't loan yourself  from yourself, silly! :)")   
                return
            # from here there are two users EXACTLY ONE of which is me
            self.db.loan(from_user,from_vault,to_user,to_vault,amount,reason)
        except:
            if(from_user==self.username):
                messagebox.showerror("Unsuccessful Loaning Transaction",f"Failed to loan {to_user.upper()}, {amount}EGP")
            elif(to_user==self.username):
                messagebox.showerror("Unsuccessful Loaning Transbaction",f'''Failed to be loaned by {from_user.upper()}, {amount}EGP
                                     maybe they lacked the money''')
            else:
                messagebox.showerror("Unsuccessful Loaning Transaction","how did this even happen??? report a bug")
        else:
            messagebox.showinfo("Successful Loaning Transaction",f"Loan was successful from {to_user} to {to_user}, {amount}EGP")
    def add_outside_user(self):
        self.destory_all_widgets()
        def add_user_then_back():
            username = self.add_user_entry.get()
            if not username:
                messagebox.showerror("invalid username","username can't be empty")
                return
            if self.db.user_exists(username):
                messagebox.showerror("invalid username","username already exists")
                return
                
            self.db.add_user(self.add_user_entry.get())
            self.loan_menu() #change later if you had to add a fake user from a different place
        self.master.title("Adding outside user")
        
        self.add_user_label = CTkLabel(self.master,text="username:")
        self.add_user_label.grid(row=0,column=0)
        self.add_user_entry = Entry(self.master)
        self.add_user_entry.grid(row=0,column=1)
        
        self.add_user_button = CTkButton(self.master,text="Add User",
                                      command=add_user_then_back)
        self.add_user_button.grid(row=1,column=0,columnspan=2)
        

    def summary_menu(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.title("Summary Menu")
        self.total_label = CTkLabel(self.master, text=f"Total Amount: {self.db.get_user_balance(self.username):.2f} EGP")
        self.total_label.pack(pady=10)

        # Display vault details
        self.vault_details_label = CTkLabel(self.master, text="Vault Details:")
        self.vault_details_label.pack(pady=2)
        vaults = self.db.get_user_vaults(self.username)
        for vault_name,balance in vaults.items():
            vault_info = f"{vault_name}: {balance:.2f} EGP"
            CTkLabel(self.master, text=vault_info).pack(pady=2)

        # Display loan information
        self.loan_details_label = CTkLabel(self.master, text="Loan Details:")
        self.loan_details_label.pack(pady=2)
        loans= self.db.get_loans(self.username)
        owes = "owes"
        for from_user,to_user,amount in loans:
            if to_user == self.username:
                to_user="YOU"
                owes = "owe"
            if from_user == self.username:
                from_user="YOU"
            loan_info = f"{to_user.upper()} {owes} {from_user.upper()} {amount:.2f}EGB"
            CTkLabel(self.master, text=loan_info).pack(pady=2)

        self.back_button = CTkButton(self.master, text="Back",fg_color="#444", text_color="white", command=lambda: self.user_menu())
        self.back_button.pack(pady=10)

        self.window_resize()

    def account_menu(self):
        for widget in self.master.winfo_children():
            widget.destroy()
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
        """ask_new_name = CTkInputDialog(text="New vault name is:", title="Add new vault")
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
            messagebox.showerror("Error", "Vault name can't be empty")"
            """
    def export_to_excel(self):
        # Replace with actual functionality
        print("Export to Excel called")
        try:
            self.db.export_to_excel(self.username)
        except PermissionError:
            messagebox.showerror("couldn't export into excel",'''close any instancesof the file, 
                                                                and make sure you have write permissions''')
         
    def destory_all_widgets(self):
         for widget in self.master.winfo_children():
            widget.destroy()
    def window_resize(self):
        self.master.update_idletasks()
        width = self.master.winfo_reqwidth()
        height = self.master.winfo_reqheight()
        margin = 20
        self.master.geometry(f"{max(width+margin,self.default_width)}x{max(height+margin,self.default_height)}")


# Main Application
root = CTk()
app = GUI(root)
root.mainloop()

