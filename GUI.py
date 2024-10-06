import customtkinter
from tkinter import * # type: ignore
from tkinter import messagebox
from Database import Database as DB
# GUI Interface
class GUI:
    def __init__(self, master):
        self.usernames = ["bob"]
        self.username = "bob"
        self.vault_names = ["vault"]
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

        self.login_button = Button(self.master, text="Login", command=self.login)
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

        self.signup_button = Button(self.master, text="Sign Up", command=self.signup)
        self.signup_button.pack(pady=10)

        self.back_button = Button(self.master, text="Back", command=self.main_menu)
        self.back_button.pack(pady=2)

    def login(self):
        self.user_menu()

    def signup(self):
        self.user_menu()

    def user_menu(self):
        self.destory_all_widgets()

        self.master.title(f"Finance Manager - {self.username}")  # Show the username in the title

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

        self.amount_label = Label(self.master, text="Amount:")
        self.amount_label.pack(pady=2)
        self.amount_entry = Entry(self.master)
        self.amount_entry.pack(pady=2)

        self.reason_label = Label(self.master, text="Reason:")
        self.reason_label.pack(pady=2)
        self.reason_entry = Entry(self.master)
        self.reason_entry.pack(pady=2)

        chosen_vault = StringVar(self.master)
        chosen_vault.set("Main")
        self.vault_options = OptionMenu(self.master,chosen_vault,*self.vault_names)
        self.vault_options.pack(pady=2)

        self.submit_button = Button(self.master, text=transaction_type, command=lambda: self.process_transaction(transaction_type,chosen_vault.get()))
        self.submit_button.pack(pady=10)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.pack(pady=2)

    def process_transaction(self, transaction_type,vault):
        pass


    def transfer_menu(self):
        self.destory_all_widgets()

        self.master.title("Transfer Menu")

        

        self.from_vault_label = Label(self.master, text="From:")
        self.from_vault_label.grid(row=0,column=0, padx=5)
        from_vault = StringVar(self.master)
        from_vault.set("Main")
        self.from_vault_options = OptionMenu(self.master,from_vault,*self.vault_names)
        self.from_vault_options.grid(row=0,column=1)

        self.to_user_label = Label(self.master, text="To user:")
        self.to_user_label.grid(row=1,column=0, padx=5)
        to_user = StringVar(self.master)
        to_user.set(self.username)
        self.to_user_options = OptionMenu(self.master,to_user,*self.usernames)
        self.to_user_options.grid(row=1,column=1)

        self.to_vault_label = Label(self.master, text="To vault:")
        self.to_vault_label.grid(row=2,column=0, padx=5)
        to_vault = StringVar(self.master)
        to_vault.set("Main")
        self.to_vault_options = OptionMenu(self.master,to_vault,*self.vault_names)
        self.to_vault_options.grid(row=2,column=1)

        self.amount_label = Label(self.master, text="Amount:")
        self.amount_label.grid(row=3,column=0, pady=2)
        self.amount_entry = Entry(self.master)
        self.amount_entry.grid(row=3,column=1, pady=2, padx=3)

        self.reason_label = Label(self.master, text="Reason:")
        self.reason_label.grid(row=4,column=0,pady=2)
        self.reason_entry = Entry(self.master)
        self.reason_entry.grid(row=4,column=1,pady=2)

        self.submit_button = Button(self.master, text="Transfer", 
                                    command=lambda: self.process_transfer(from_vault.get(),to_user.get(),to_vault.get(),self.amount_entry.get()))
        self.submit_button.grid(row=5,column=1, pady=10)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.grid(row=6,column=1, pady=2)


    def process_transfer(self,from_vault,to_user,to_vault,amount):
        pass


    def loan_menu(self):
        self.destory_all_widgets()

        self.master.title("Loan Menu")

        self.amount_label = Label(self.master, text="Amount:")
        self.amount_label.pack(pady=2)
        self.amount_entry = Entry(self.master)
        self.amount_entry.pack(pady=2)

        self.reason_label = Label(self.master, text="Reason:")
        self.reason_label.pack(pady=2)
        self.reason_entry = Entry(self.master)
        self.reason_entry.pack(pady=2)

        self.person_label = Label(self.master, text="Person:")
        self.person_label.pack(pady=2)
        self.person_entry = Entry(self.master)
        self.person_entry.pack(pady=2)

        self.submit_button = Button(self.master, text="Record Loan", command=lambda: self.process_loan())
        self.submit_button.pack(pady=10)

        self.back_button = Button(self.master, text="Back", command=lambda: self.user_menu())
        self.back_button.pack(pady=2)

    def process_loan(self):
        pass


    def summary_menu(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.title("Summary Menu")
        self.total_label = Label(self.master, text=f"Total Amount: {self.get_balance():.2f} EGP")
        self.total_label.pack(pady=10)

        # Display vault details
        self.vault_details_label = Label(self.master, text="Vault Details:")
        self.vault_details_label.pack(pady=2)
        for vault in self.get_vaults():
            vault_info = f"{vault["name"]}: {vault["balance"]:.2f} EGP"
            Label(self.master, text=vault_info).pack(pady=2)

        # Display loan information
        #c.execute("SELECT * FROM loans WHERE username = ?", (username,))
        #loans = c.fetchall()
        #self.loan_details_label = Label(self.master, text="Loan Details:")
        #self.loan_details_label.pack(pady=2)
        #for loan in loans:
        #    loan_info = f"Amount: {loan[1]:.2f} EGP, Reason: {loan[2]}, Person: {loan[3]}"  # Assuming loan[1] is amount, loan[2] is reason, and loan[3] is person
        #    Label(self.master, text=loan_info).pack(pady=2)

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

        self.logout_button = Button(self.master, text="Logout", command=self.main_menu)
        self.logout_button.pack(pady=2)

        self.back_button = Button(self.master, text="Back", command=self.user_menu)
        self.back_button.pack(pady=2)
    def add_vault(self):
        ask_new_name = customtkinter.CTkInputDialog(text="New vault name is:", title="Add new vault")
        new_name = ask_new_name.get_input()
        if new_name:
            messagebox.showinfo("Success", f"Vault '{new_name}' added successfully!")
        elif new_name=="":
            messagebox.showerror("Error", "Vault name can't be empty")
             
    def get_balance(self):
        return 0
    def get_vaults(self):
        return [{"name":"main","balance":0}]
    def destory_all_widgets(self):
         for widget in self.master.winfo_children():
            widget.destroy()


# Main Application
root = Tk()
app = GUI(root)
root.mainloop()

