
import sqlite3
from tkinter import messagebox
class Database:
    def __init__(self, db_name='financial_manager2.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        #if pass is null they arnet a user 
        #but just some one you loan with
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT 
        )
        ''')

        # Create vaults table
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS vaults (
            vault_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            balance REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            UNIQUE (vault_name, user_id)
        )
        ''')

        # Create transactions table
        #make sure to lower case non-list items (like description)
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,         -- The amount of money spent
            category_id INTEGER,
            description TEXT NOT NULL,    -- General purpose for what was bought or paid for
            quantity REAL,                -- Quantity of the item or service
            unit_id  INTEGER,                    -- The unit of measurement (e.g., "kg", "pcs")
            date TEXT NOT NULL,
            FOREIGN KEY (vault_id) REFERENCES vaults (vault_id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE SET NULL,
            FOREIGN KEY (unit_id) REFERENCES units (unit_id) ON DELETE SET NULL
        )
        ''')
        # Create loan table
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            from_vault_id NOT NULL,
            to_vault_id NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (from_vault_id, to_vault_id),
            FOREIGN KEY (from_vault_id) REFERENCES vaults (vault_id),
            FOREIGN KEY (to_vault_id) REFERENCES vaults (vault_id)
        )
        ''')

        self.c.execute(''' 
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
        ''')

        self.c.execute('''
            CREATE TABLE IF NOT EXISTS units (
                unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_name TEXT NOT NULL UNIQUE
            );
        ''')
        self.conn.commit()

    def close(self):
        self.conn.close()

    #database accessing

    #users
    def get_user_id(self,username):
        username = str(username)
        username = username.capitalize()
        self.c.execute("SELECT user_id FROM users WHERE username = ?",(username,))
        user_id = self.c.fetchone()[0]
        return user_id
    def get_usernames(self):
        self.c.execute("SELECT username FROM users")
        res = self.c.fetchall()
        usernames = [username[0] for username in res]
        return usernames
    def user_exists(self,username):
        #check if user exists
        username = str(username)
        username = username.capitalize()
        self.c.execute("SELECT * FROM users WHERE username = ? ", 
                       (username,))
        user = self.c.fetchone()
        return user
    def check_user_password(self,username,password):
        username = str(username)
        username = username.capitalize()
        self.c.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                       (username,password))
        hasPassword = self.c.fetchone()
        return bool(hasPassword)
    def add_user(self,username,password=None):
        #adds user if it doesnt exist already
        username = str(username)
        username = username.capitalize()
        if self.user_exists(username):
            raise Exception("Can't add auser that exists")
        self.c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, password))
        user_id = self.get_user_id(username)
        self.c.execute("INSERT INTO vaults (user_id,vault_name,balance) VALUES (?,?,0)",
                       (user_id,"Main"))
        self.conn.commit()
        return True
    
    #vaults
    def get_vault_id(self,username,vault_name):
        user_id = self.get_user_id(username)
        self.c.execute("SELECT vault_id FROM vaults WHERE user_id = ? AND vault_name = ?", (user_id,vault_name))
        vault_id = self.c.fetchone()[0]
        return vault_id
    def vault_exists(self,username,vault_name):
        #check if vault exists
        username = str(username)
        username = username.capitalize()
        user_id = self.get_user_id(username)
        self.c.execute("SELECT * FROM vaults WHERE user_id = ? AND vault_name = ?",
                        (user_id, vault_name))
        vault = self.c.fetchone()
        return vault
    def add_vault(self,username,vault_name):
        username = str(username)
        username = username.capitalize()
        user_id = self.get_user_id(username)
        #adds vault if it doesnt exist already
        vault_name = vault_name.capitalize() #Make sure all vault names start with capital letter
        if self.vault_exists(username,vault_name):
            return False
        self.c.execute("INSERT INTO vaults (user_id,vault_name,balance) VALUES (?,?,0)",
                       (user_id,vault_name))
        self.conn.commit()
        return True
    def remove_vault(self,username,vault_name):
        #removes a vault
        # would require transfering all the money in it into the users Main vault
        # also the Main vault can't be deleted and all vault names start with a capital letter
        pass
    def vault_has_balance(self,username,vault_name,amount):
        username = str(username)
        username = username.capitalize()
        user_id = self.get_user_id(username)
        self.c.execute("SELECT balance FROM vaults WHERE user_id = ? AND vault_name = ?",(user_id,vault_name))
        balance = self.c.fetchone()[0]
        try:
            balance = float(balance)
            amount = float(amount)
        except TypeError:
            messagebox.showerror("incorrect amount", "money amount must be an integer")
        return balance>=amount
    def add_to_vault(self,username,vault_name,amount):
        username = str(username)
        username = username.capitalize()
        user_id = self.get_user_id(username)
        self.c.execute("UPDATE vaults SET balance = balance + ? WHERE user_id = ? AND vault_name = ?",
                    (amount, user_id,vault_name)) 
        return True
    def remove_from_vault(self,username,vault_name,amount):
        username = str(username)
        username = username.capitalize()
        if not self.vault_has_balance(username,vault_name,amount):
            raise ValueError("insufficent funds")
        user_id = self.get_user_id(username)
        self.c.execute("UPDATE vaults SET balance = balance - ? WHERE user_id = ? AND vault_name = ?",
                    (amount, user_id,vault_name)) 
        return True
    def get_user_vault_names(self,username):
        username = str(username)
        username = username.capitalize()
        user_id = self.get_user_id(username)
        self.c.execute("SELECT vault_name FROM vaults WHERE user_id = ?",(user_id,))
        vaults = self.c.fetchall()
        vault_names = [vault[0] for vault in vaults]
        return vault_names
    def get_user_vaults(self,username):
        username = str(username)
        username = username.capitalize()
        user_id = self.get_user_id(username)
        self.c.execute("SELECT vault_name,balance FROM vaults WHERE user_id = ?",(user_id,))
        vaults = self.c.fetchall()
        vault_dict={}
        for vault_name,balance in vaults:
            vault_dict[vault_name]=balance
        return vault_dict
    def get_user_balance(self,username):
        username = username.capitalize()
        user_id = self.get_user_id(username)
        self.c.execute("SELECT balance FROM vaults WHERE user_id = ?",(user_id,))
        balances = self.c.fetchall()
        total_balance = 0
        for balance in balances:
            total_balance+=balance[0]
        return total_balance
    #transactions
    def add_transaction(self,username,vault_name,transaction_type,money_amount,category,description,quantity=None,unit=None):
        vault_id = self.get_vault_id(username,vault_name)
        category_id = self.get_category_id(category)
        unit_id = self.get_unit_id(unit)
        self.c.execute('''INSERT INTO transactions 
                       (vault_id, transaction_type,amount,category_id, description, quantity,unit_id,date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                  ''', 
                (vault_id,transaction_type,money_amount,category_id,description.lower(),quantity,unit_id))
        self.conn.commit()
        return True
    #loans
    

    def add_loan(self,from_user,from_vault,to_user,to_vault,money_amount):
        from_vault_id = self.get_vault_id(from_user,from_vault)
        to_vault_id = self.get_vault_id(to_user,to_vault)
        def loan_exists():
            self.c.execute("SELECT * FROM loans WHERE from_vault_id= ? AND to_vault_id= ?",
                           (from_vault_id,to_vault_id))
            loan = self.c.fetchall()
            return len(loan)>=1
        if(loan_exists()):
            self.c.execute("""UPDATE loans 
                            SET amount = amount + ?
                            WHERE from_vault_id = ? AND to_vault_id = ?""",
                            (money_amount,from_vault_id,to_vault_id))
        else:
            self.c.execute("INSERT INTO loans (from_vault_id,to_vault_id,amount) VALUES(?,?,?)",
                           (from_vault_id,to_vault_id,money_amount))
        self.conn.commit()
        
    def get_loans(self, username):
        query = '''
        SELECT 
            u_from.username AS from_user,
            u_to.username AS to_user,
            SUM(l.amount) AS total_sum
        FROM loans l
        JOIN vaults v_from ON l.from_vault_id = v_from.vault_id
        JOIN vaults v_to ON l.to_vault_id = v_to.vault_id
        JOIN users u_from ON v_from.user_id = u_from.user_id
        JOIN users u_to ON v_to.user_id = u_to.user_id
        WHERE u_from.username = ? OR u_to.username = ?
        GROUP BY u_from.username, u_to.username
        '''
        self.c.execute(query, (username, username))
        results = self.c.fetchall()
        return results
    #categories
    def get_category_id(self,category):
        self.c.execute("SELECT category_id FROM categories WHERE category_name = ?",(category,))
        category_id = self.c.fetchone()[0]
        return category_id
    
    def get_category_names(self):
        self.c.execute("SELECT category_name FROM categories")
        categories = self.c.fetchall()
        category_names = [category[0] for category in  categories]
        return category_names
    #units
    def get_unit_id(self,unit_name):
        if not unit_name:
            return None
        self.c.execute("SELECT unit_id FROM units WHERE unit_name = ?",(unit_name,))
        unit_id = self.c.fetchone()[0]
        return unit_id
    def get_unit_names(self):
        self.c.execute("SELECT unit_name FROM units")
        units = self.c.fetchall()
        unit_names = [unit[0] for unit in  units]
        return unit_names
    #services
    def deposit(self,username,vault_name,amount,category_name,description,quantity=None,unit=None):
        self.add_to_vault(username,vault_name,amount)
        self.add_transaction(username,vault_name,"Deposit",float(amount),category_name,description,quantity,unit)
        return True
    
    def withdraw(self,username,vault_name,amount,category_name,description,quantity=None,unit=None):
        self.remove_from_vault(username,vault_name,amount)
        self.add_transaction(username,vault_name,"Withdraw",-float(amount),category_name,description,quantity,unit)
        return True
    def transfer(self,from_user,from_vault,to_user,to_vault,amount,description=None,is_loan_=False):
        transaction_type= "Loan" if is_loan_ else "Transfer"
        description = description if description else f"{transaction_type}ing money" 
        self.remove_from_vault(from_user,from_vault,amount)
        self.add_to_vault(to_user,to_vault,amount)
        self.add_transaction(from_user,from_vault,transaction_type,-float(amount),"Others",description)
        self.add_transaction(to_user,to_vault,transaction_type,amount,"Others",description)

    def loan(self,from_user,from_vault,to_user,to_vault,amount,description=None):
        self.transfer(from_user,from_vault,to_user,to_vault,amount,description,is_loan_=True)
        self.add_loan(from_user,from_vault,to_user,to_vault,amount)
        
        