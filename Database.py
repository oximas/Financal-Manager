from email import message
import sqlite3
from tkinter import messagebox
class Database:
    def __init__(self, db_name='financial_manager2.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        #if pass is null theu arnet a user 
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
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE (vault_name, user_id)
        )
        ''')

        # Create transactions table
        #make sure to lower case non-list items (like description)
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vault_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,         -- The amount of money spent
            category_id INTEGER NOT NULL,
            description TEXT NOT NULL,    -- General purpose for what was bought or paid for
            quantity REAL,                -- Quantity of the item or service
            unit_id  INTEGER,                    -- The unit of measurement (e.g., "kg", "pcs")
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (vault_id) REFERENCES vaults (vault_id),
            FOREIGN KEY (category_id) REFERENCES categories (category_id)
            FOREIGN KEY (unit_id) REFERENCES units (unit_id)
        )
        ''')
        # Create loan table
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            from_id INT NOT NULL,
            to_id INT NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (from_id , to_id),
            FOREIGN KEY (from_id) REFERENCES users (user_id) 
            FOREIGN KEY (to_id) REFERENCES users (user_id)
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
            return False
        self.c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, password))
        user_id = self.get_user_id(username)
        self.c.execute("INSERT INTO vaults (user_id,vault_name,balance) VALUES (?,?,0)",
                       (user_id,"Main"))
        self.conn.commit()
        return True
    
    #vaults
    def get_vault_id(self,vault_name):
        self.c.execute("SELECT vault_id FROM vaults WHERE vault_name = ?", (vault_name,))
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
            return False
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
        self.c.execute("SELECT (vault_name,balance) FROM vaults WHERE user_id = ?",(user_id,))
        vaults = self.c.fetchall()
        return dict(vaults)
    #transactions
    def add_transaction(self,username,vault_name,transaction_type,money_amount,category,description,quantity=None,unit=None):
        user_id = self.get_user_id(username)
        vault_id = self.get_vault_id(vault_name)
        category_id = self.get_category_id(category)
        unit_id = self.get_unit_id(unit)
        self.c.execute('''INSERT INTO transactions 
                       (user_id, vault_id, transaction_type,amount,category_id, description, quantity,unit_id,date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                  ''', 
                (user_id,vault_id,transaction_type,money_amount,category_id,description.lower(),quantity,unit_id))
        self.conn.commit()
        return True

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
        self.add_transaction(username,vault_name,"Deposit",float(amount),category_name,description,float(quantity),unit)
        return True
    def withdraw(self,username,vault_name,amount,category_name,description,quantity=None,unit=None):
        self.remove_from_vault(username,vault_name,amount)
        self.add_transaction(username,vault_name,"Withdraw",-float(amount),category_name,description,float(quantity),unit)
        return True
    