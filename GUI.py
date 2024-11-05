import tkinter as tk
import customtkinter
from tkinter import * # type: ignore
from tkinter import messagebox
from Database import Database as DB
# GUI Interface
class GUI:
    def __init__(self, master):

        self.db = DB("personal_financial_manager.db")

        self.master = master
        self.master.title("Finance Manager")
        self.master.geometry("400x300")

        self.main_menu()  # Calls the menu with login/signup options

    def main_menu(self):
        self.destory_all_widgets()
        self.master.title("Finance Manager - Welcome")

        self.login_button = Button(self.master, text="Login", command=self.login_menu)
        self.login_button.pack(pady=10)

        self.signup_button = Button(self.master, text="Sign Up", command=self.signup_menu)
        self.signup_button.pack(pady=10)
    def login_menu(self):
        self.destory_all_widgets()

        self.master.title("Login")

        self.username_label = Label(self.master, text="Username:")
        self.username_label.pack(pady=2)
        self.username_entry = Entry(self.master)
        self.username_entry.pack(pady=2)

        self.password_label = Label(self.master, text="Password:")
        self.password_label.pack(pady=2)
        self.password_entry = Entry(self.master, show="*")
        self.password_entry.pack(pady=2)

        self.login_button = Button(self.master, text="Login", command=lambda : self.login(self.username_entry.get()
                                                                                          ,self.password_entry.get()))
        self.login_button.pack(pady=10)

        self.back_button = Button(self.master, text="Back", command=self.main_menu)
        self.back_button.pack(pady=2)

    def signup_menu(self):
        self.destory_all_widgets()

        self.master.title("Sign Up")

        self.username_label = Label(self.master, text="Username:")
        self.username_label.pack(pady=2)
        self.username_entry = Entry(self.master)
        self.username_entry.pack(pady=2)

        self.password_label = Label(self.master, text="Password:")
        self.password_label.pack(pady=2)
        self.password_entry = Entry(self.master, show="*")
        self.password_entry.pack(pady=2)

        self.confirm_password_label = Label(self.master, text="Confirm Password:")
        self.confirm_password_label.pack(pady=2)
        self.confirm_password_entry = Entry(self.master, show="*")
        self.confirm_password_entry.pack(pady=2)

        self.signup_button = Button(self.master, text="Sign Up", command=lambda : self.signup(self.username_entry.get(),
                                                                                              self.password_entry.get(),
                                                                                              self.confirm_password_entry.get()))
        self.signup_button.pack(pady=10)

        self.back_button = Button(self.master, text="Back", command=self.main_menu)
        self.back_button.pack(pady=2)

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

        self.deposit_button = Button(self.master, text="Deposit", command=self.deposit_menu)
        self.deposit_button.pack(pady=2)

        self.withdraw_button = Button(self.master, text="Withdraw", command=self.withdraw_menu)
        self.withdraw_button.pack(pady=2)

        self.transfer_button = Button(self.master, text="Transfer", command=self.transfer_menu)
        self.transfer_button.pack(pady=2)

        self.loan_button = Button(self.master, text="Loan", command=self.loan_menu)
        self.loan_button.pack(pady=2)

        self.summary_button = Button(self.master, text="Summary", command=self.summary_menu)
        self.summary_button.pack(pady=2)

        self.account_button = Button(self.master, text="Account", command=self.account_menu)
        self.account_button.pack(pady=2)
        


    def deposit_menu(self):
        self.transaction_menu("Deposit")

    def withdraw_menu(self):
        self.transaction_menu("Withdraw")

    def transaction_menu(self, transaction_type):
        self.destory_all_widgets()

        self.master.title(f"{transaction_type} Menu")

        self.amount_label = Label(self.master, text="Money Amount:")
        self.amount_label.pack(pady=2)
        self.amount_entry = Entry(self.master)
        self.amount_entry.pack(pady=2)

        self.category_label = Label(self.master, text="Category:")
        self.category_label.pack()
        category_names = self.db.get_category_names()
        chosen_category = StringVar(self.master)
        chosen_category.set(category_names[0] if len(category_names) else "Please add more categories")
        self.category_options = OptionMenu(self.master,chosen_category,*category_names)
        self.category_options.pack()

        self.description_label = Label(self.master, text="Description:")
        self.description_label.pack(pady=2)
        self.description_entry = Entry(self.master)
        self.description_entry.pack(pady=2)

        if(transaction_type=="Withdraw"):
            self.quantity_label = Label(self.master, text="Quantity:")
            self.quantity_label.pack(pady=2)
            self.quantity_entry = Entry(self.master)
            self.quantity_entry.pack(pady=2)

            self.unit_label = Label(self.master, text="Unit:")
            self.unit_label.pack()
            unit_names = self.db.get_unit_names()
            chosen_unit = StringVar(self.master)
            chosen_unit.set(unit_names[0] if len(unit_names) else "Please add more units")
            self.unit_options = OptionMenu(self.master,chosen_unit,*unit_names)
            self.unit_options.pack()

        self.vault_label = Label(self.master, text="Vault:")
        self.vault_label.pack()
        chosen_vault = StringVar(self.master)
        chosen_vault.set("Main")
        self.vault_options = OptionMenu(self.master,chosen_vault,*self.db.get_user_vault_names(self.username))
        self.vault_options.pack(pady=2)
        if(transaction_type=="Withdraw"):
            self.submit_button = Button(self.master, text=transaction_type, 
                                        command=lambda: self.process_transaction(transaction_type,chosen_vault.get(),
                                                                                self.amount_entry.get(),chosen_category.get(),
                                                                                self.description_entry.get(),self.quantity_entry.get(),
                                                                                chosen_unit.get()))
        elif transaction_type=="Deposit":
            self.submit_button = Button(self.master, text=transaction_type, 
                                        command=lambda: self.process_transaction(transaction_type,chosen_vault.get(),
                                                                                self.amount_entry.get(),chosen_category.get(),
                                                                                self.description_entry.get()))
        else:
            raise ValueError("transaction type must be 'Withdraw' or 'Deposit' ")
        self.submit_button.pack(pady=10)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.pack(pady=2)

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

        from_vault_names = self.db.get_user_vault_names(self.username)

        self.from_vault_label = Label(self.master, text="From:")
        self.from_vault_label.grid(row=0,column=0, padx=5)
        from_vault = StringVar(self.master)
        from_vault.set(from_vault_names[0])
        self.from_vault_options = OptionMenu(self.master,from_vault,*from_vault_names)
        self.from_vault_options.grid(row=0,column=1)

        self.to_user_label = Label(self.master, text="To user:")
        self.to_user_label.grid(row=1,column=0, padx=5)
        to_user = StringVar(self.master)
        to_user.set(self.username)
        self.to_user_options = OptionMenu(self.master,to_user,*self.db.get_usernames(), command=lambda username:refresh_to_user_vault_names(username))
        self.to_user_options.grid(row=1,column=1)

        to_vault_names = self.db.get_user_vault_names(to_user.get())
        self.to_vault_label = Label(self.master, text="To vault:")
        self.to_vault_label.grid(row=2,column=0, padx=5)
        to_vault = StringVar(self.master)
        to_vault.set(to_vault_names[0])
        self.from_vault_options = OptionMenu(self.master,to_vault,*to_vault_names)
        self.from_vault_options.grid(row=2,column=1)

        self.amount_label = Label(self.master, text="Amount:")
        self.amount_label.grid(row=3,column=0, pady=2)
        self.amount_entry = Entry(self.master)
        self.amount_entry.grid(row=3,column=1, pady=2, padx=3)

        self.reason_label = Label(self.master, text="Reason(not required):")
        self.reason_label.grid(row=4,column=0,pady=2)
        self.reason_entry = Entry(self.master)
        self.reason_entry.grid(row=4,column=1,pady=2)

        self.submit_button = Button(self.master, text="Transfer", 
                                    command=lambda: self.process_transfer(from_vault.get(),to_user.get(),to_vault.get(),
                                                                          self.amount_entry.get(),self.reason_entry.get()))
        self.submit_button.grid(row=5,column=1, pady=10)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.grid(row=6,column=1, pady=2)

        def refresh_to_user_vault_names(username):
            to_vault_names = self.db.get_user_vault_names(username)
            to_vault.set(to_vault_names[0])
            self.from_vault_options['menu'].delete(0,'end')
            for vault in to_vault_names:
                self.from_vault_options['menu'].add_command(label=vault,command=lambda v=vault: to_vault.set(v))
        def refresh_from_user_vault_names(username):
            from_vault_names = self.db.get_user_vault_names(username)
            from_vault.set(from_vault_names[0])
            self.from_vault_options['menu'].delete(0,'end')
            for vault in from_vault_names:
                self.from_vault_options['menu'].add_command(label=vault,command=lambda:tk._setit(to_vault,vault))


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

        self.from_user_label = Label(self.master, text="From user:")
        self.from_user_label.grid(row=0,column=0, padx=5)
        from_user = StringVar(self.master)
        from_user.set(self.username)
        self.from_user_options = OptionMenu(self.master,from_user,*self.db.get_usernames(), command=lambda username:refresh_from_user_vault_names(username))
        self.from_user_options.grid(row=0,column=1)

        from_vault_names = self.db.get_user_vault_names(from_user.get())
        self.from_vault_label = Label(self.master, text="From vault:")
        self.from_vault_label.grid(row=1,column=0, padx=5)
        from_vault = StringVar(self.master)
        from_vault.set(from_vault_names[0])
        self.from_vault_options = OptionMenu(self.master,from_vault,*from_vault_names)
        self.from_vault_options.grid(row=1,column=1)
        
        #self.add_outside_user_button = Button(self.master,text="Add outside user",command=lambda: self.add_outside_user())
        #self.add_outside_user_button.grid(row=2,column=0,columnspan=2)

        self.to_user_label = Label(self.master, text="To user:")
        self.to_user_label.grid(row=3,column=0, padx=5)
        to_user = StringVar(self.master)
        to_user.set(self.username)
        self.to_user_options = OptionMenu(self.master,to_user,*usernames,command=lambda x:refresh_to_user_vault_names(to_user.get()))
        self.to_user_options.grid(row=3,column=1)

        self.to_vault_label = Label(self.master, text="To vault:")
        self.to_vault_label.grid(row=4,column=0, padx=5)
        to_vault = StringVar(self.master)
        to_vault.set(vault_names[0])
        self.to_vault_options = OptionMenu(self.master,to_vault,*vault_names)
        self.to_vault_options.grid(row=4,column=1)

        self.amount_label = Label(self.master, text="Amount:")
        self.amount_label.grid(row=5,column=0, pady=2)
        self.amount_entry = Entry(self.master)
        self.amount_entry.grid(row=5,column=1, pady=2, padx=3)

        self.reason_label = Label(self.master, text="Reason(not required):")
        self.reason_label.grid(row=6,column=0,pady=2)
        self.reason_entry = Entry(self.master)
        self.reason_entry.grid(row=6,column=1,pady=2)

        self.submit_button = Button(self.master, text="Loan", 
                                    command=lambda: self.process_loan(from_user.get(),from_vault.get(),to_user.get(),from_vault.get(),
                                                                          self.amount_entry.get(),self.reason_entry.get()))
        self.submit_button.grid(row=7,column=1, pady=10)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.grid(row=8,column=1, pady=2)

        def refresh_to_user_vault_names(username):
            to_vault_names = self.db.get_user_vault_names(username)
            to_vault.set(to_vault_names[0])
            self.to_vault_options['menu'].delete(0,'end')
            for vault in to_vault_names:
                self.to_vault_options['menu'].add_command(label=vault,command=lambda v=vault: to_vault.set(v))
        def refresh_from_user_vault_names(username):
            from_vault_names = self.db.get_user_vault_names(username)
            from_vault.set(from_vault_names[0])
            self.from_vault_options['menu'].delete(0,'end')
            for vault in from_vault_names:
                self.from_vault_options['menu'].add_command(label=vault,command=lambda v=vault: from_vault.set(v))
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
        
        self.add_user_label = Label(self.master,text="username:")
        self.add_user_label.grid(row=0,column=0)
        self.add_user_entry = Entry(self.master)
        self.add_user_entry.grid(row=0,column=1)
        
        self.add_user_button = Button(self.master,text="Add User",
                                      command=add_user_then_back)
        self.add_user_button.grid(row=1,column=0,columnspan=2)
        

    def summary_menu(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.title("Summary Menu")
        self.total_label = Label(self.master, text=f"Total Amount: {self.db.get_user_balance(self.username):.2f} EGP")
        self.total_label.pack(pady=10)

        # Display vault details
        self.vault_details_label = Label(self.master, text="Vault Details:")
        self.vault_details_label.pack(pady=2)
        vaults = self.db.get_user_vaults(self.username)
        for vault_name,balance in vaults.items():
            vault_info = f"{vault_name}: {balance:.2f} EGP"
            Label(self.master, text=vault_info).pack(pady=2)

        # Display loan information
        self.loan_details_label = Label(self.master, text="Loan Details:")
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
            Label(self.master, text=loan_info).pack(pady=2)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.pack(pady=10)
    def account_menu(self):
        for widget in self.master.winfo_children():
            widget.destroy()
        self.username_label = Label(self.master,text=f"Username: {self.username}")
        self.username_label.pack(pady=2)

        self.add_vault_button = Button(self.master,text="Add vault", command = self.add_vault)
        self.add_vault_button.pack(pady=2)

        self.change_password_button = Button(self.master,text="Change password")
        self.change_password_button.pack(pady=2)

        self.export_button = tk.Button(self.master, text="Export data to Excel", command=self.export_to_excel)
        self.export_button.pack(pady=10)
        
        self.logout_button = Button(self.master, text="Logout", command=self.main_menu)
        self.logout_button.pack(pady=2)

        self.back_button = Button(self.master, text="Back", command=self.user_menu)
        self.back_button.pack(pady=2)
    def add_vault(self):
        ask_new_name = customtkinter.CTkInputDialog(text="New vault name is:", title="Add new vault")
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
         
    def destory_all_widgets(self):
         for widget in self.master.winfo_children():
            widget.destroy()


# Main Application
root = Tk()
app = GUI(root)
root.mainloop()

