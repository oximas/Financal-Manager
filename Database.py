# Database.py
"""
Database access layer for the Finance Manager application.
Handles all database operations including users, vaults, transactions, and loans.
"""
import sqlite3
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import pandas as pd
from tkinter import filedialog


class InsufficientFundsError(Exception):
    """Raised when attempting to withdraw more money than available"""
    pass


class Database:
    """
    Database access layer for financial data.
    Provides methods for CRUD operations on users, vaults, transactions, and loans.
    """
    
    def __init__(self, db_name: str = 'financial_manager2.db'):
        """
        Initialize database connection and create tables.
        
        Args:
            db_name: Name of the SQLite database file
        """
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self) -> None:
        """Create all required database tables if they don't exist"""
        self._create_users_table()
        self._create_vaults_table()
        self._create_transactions_table()
        self._create_loans_table()
        self._create_categories_table()
        self._create_units_table()
        self.conn.commit()
    
    def _create_users_table(self) -> None:
        """Create the users table"""
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT
            )
        ''')
    
    def _create_vaults_table(self) -> None:
        """Create the vaults table"""
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
    
    def _create_transactions_table(self) -> None:
        """Create the transactions table"""
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vault_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER,
                description TEXT NOT NULL,
                quantity REAL,
                unit_id INTEGER,
                date TEXT NOT NULL,
                FOREIGN KEY (vault_id) REFERENCES vaults (vault_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE SET NULL,
                FOREIGN KEY (unit_id) REFERENCES units (unit_id) ON DELETE SET NULL
            )
        ''')
    
    def _create_loans_table(self) -> None:
        """Create the loans table"""
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                from_vault_id INTEGER NOT NULL,
                to_vault_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                PRIMARY KEY (from_vault_id, to_vault_id),
                FOREIGN KEY (from_vault_id) REFERENCES vaults (vault_id),
                FOREIGN KEY (to_vault_id) REFERENCES vaults (vault_id)
            )
        ''')
    
    def _create_categories_table(self) -> None:
        """Create the categories table"""
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL UNIQUE
            )
        ''')
    
    def _create_units_table(self) -> None:
        """Create the units table"""
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS units (
                unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_name TEXT NOT NULL UNIQUE
            )
        ''')
    
    def close(self) -> None:
        """Close the database connection"""
        self.conn.close()
    
    # ==================== USER OPERATIONS ====================
    
    @staticmethod
    def _normalize_username(username: str) -> str:
        """
        Normalize username to consistent format (capitalized).
        
        Args:
            username: Raw username input
            
        Returns:
            Normalized username
        """
        return str(username).capitalize()
    
    def get_user_id(self, username: str) -> int:
        """
        Get user ID for a given username.
        
        Args:
            username: The username to look up
            
        Returns:
            User ID
            
        Raises:
            TypeError: If username doesn't exist
        """
        username = self._normalize_username(username)
        self.c.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = self.c.fetchone()
        if result is None:
            raise ValueError(f"User '{username}' does not exist")
        return result[0]
    
    def get_usernames(self) -> List[str]:
        """
        Get list of all usernames.
        
        Returns:
            List of usernames
        """
        self.c.execute("SELECT username FROM users")
        results = self.c.fetchall()
        return [username[0] for username in results]
    
    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists in the database.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        username = self._normalize_username(username)
        self.c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return self.c.fetchone() is not None
    
    def check_user_password(self, username: str, password: str) -> bool:
        """
        Verify user password.
        
        Args:
            username: Username to check
            password: Password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        username = self._normalize_username(username)
        self.c.execute(
            "SELECT 1 FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        return self.c.fetchone() is not None
    
    def add_user(self, username: str, password: Optional[str] = None) -> bool:
        """
        Add a new user to the database.
        Creates a default "Main" vault for the user.
        
        Args:
            username: Username for the new user
            password: Optional password
            
        Returns:
            True if user was added successfully
            
        Raises:
            Exception: If user already exists
        """
        username = self._normalize_username(username)
        
        if self.user_exists(username):
            raise Exception("Can't add a user that exists")
        
        self.c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        
        user_id = self.get_user_id(username)
        self.c.execute(
            "INSERT INTO vaults (user_id, vault_name, balance) VALUES (?, ?, 0)",
            (user_id, "Main")
        )
        
        self.conn.commit()
        return True
    
    # ==================== VAULT OPERATIONS ====================
    
    def get_vault_id(self, username: str, vault_name: str) -> int:
        """
        Get vault ID for a specific user and vault name.
        
        Args:
            username: Owner of the vault
            vault_name: Name of the vault
            
        Returns:
            Vault ID
            
        Raises:
            ValueError: If vault doesn't exist
        """
        user_id = self.get_user_id(username)
        self.c.execute(
            "SELECT vault_id FROM vaults WHERE user_id = ? AND vault_name = ?",
            (user_id, vault_name)
        )
        result = self.c.fetchone()
        if result is None:
            raise ValueError(f"Vault '{vault_name}' does not exist for user '{username}'")
        return result[0]
    
    def vault_exists(self, username: str, vault_name: str) -> bool:
        """
        Check if a vault exists for a user.
        
        Args:
            username: Owner of the vault
            vault_name: Name of the vault
            
        Returns:
            True if vault exists, False otherwise
        """
        username = self._normalize_username(username)
        try:
            user_id = self.get_user_id(username)
            self.c.execute(
                "SELECT 1 FROM vaults WHERE user_id = ? AND vault_name = ?",
                (user_id, vault_name)
            )
            return self.c.fetchone() is not None
        except ValueError:
            return False
    
    def add_vault(self, username: str, vault_name: str) -> bool:
        """
        Add a new vault for a user.
        
        Args:
            username: Owner of the vault
            vault_name: Name of the new vault
            
        Returns:
            True if vault was added successfully
            
        Raises:
            ValueError: If vault already exists
        """
        username = self._normalize_username(username)
        user_id = self.get_user_id(username)
        vault_name = vault_name.capitalize()
        
        if self.vault_exists(username, vault_name):
            raise ValueError("Can't have duplicate vaults")
        
        self.c.execute(
            "INSERT INTO vaults (user_id, vault_name, balance) VALUES (?, ?, 0)",
            (user_id, vault_name)
        )
        self.conn.commit()
        return True
    
    def vault_has_balance(self, username: str, vault_name: str, amount: float) -> bool:
        """
        Check if a vault has sufficient balance.
        
        Args:
            username: Owner of the vault
            vault_name: Name of the vault
            amount: Amount to check against
            
        Returns:
            True if vault has sufficient balance, False otherwise
        """
        username = self._normalize_username(username)
        user_id = self.get_user_id(username)
        
        self.c.execute(
            "SELECT balance FROM vaults WHERE user_id = ? AND vault_name = ?",
            (user_id, vault_name)
        )
        result = self.c.fetchone()
        
        if result is None:
            return False
        
        balance = float(result[0])
        amount = float(amount)
        
        return balance >= amount
    
    def add_to_vault(self, username: str, vault_name: str, amount: float) -> bool:
        """
        Add money to a vault.
        
        Args:
            username: Owner of the vault
            vault_name: Name of the vault
            amount: Amount to add
            
        Returns:
            True if successful
        """
        username = self._normalize_username(username)
        user_id = self.get_user_id(username)
        
        self.c.execute(
            "UPDATE vaults SET balance = balance + ? WHERE user_id = ? AND vault_name = ?",
            (amount, user_id, vault_name)
        )
        self.conn.commit()
        return True
    
    def remove_from_vault(
        self,
        username: str,
        vault_name: str,
        amount: float,
        on_insufficient_funds: Callable[[], None]
    ) -> bool:
        """
        Remove money from a vault.
        
        Args:
            username: Owner of the vault
            vault_name: Name of the vault
            amount: Amount to remove
            on_insufficient_funds: Callback for insufficient funds
            
        Returns:
            True if successful
            
        Raises:
            InsufficientFundsError: If vault has insufficient balance
        """
        username = self._normalize_username(username)
        
        if not self.vault_has_balance(username, vault_name, amount):
            on_insufficient_funds()
            raise InsufficientFundsError(f"Insufficient funds in vault '{vault_name}'")
        
        user_id = self.get_user_id(username)
        self.c.execute(
            "UPDATE vaults SET balance = balance - ? WHERE user_id = ? AND vault_name = ?",
            (amount, user_id, vault_name)
        )
        self.conn.commit()
        return True
    
    def get_user_vault_names(self, username: str) -> List[str]:
        """
        Get list of vault names for a user.
        
        Args:
            username: User to get vaults for
            
        Returns:
            List of vault names
        """
        username = self._normalize_username(username)
        user_id = self.get_user_id(username)
        
        self.c.execute(
            "SELECT vault_name FROM vaults WHERE user_id = ?",
            (user_id,)
        )
        vaults = self.c.fetchall()
        return [vault[0] for vault in vaults]
    
    def get_user_vaults(self, username: str) -> Dict[str, float]:
        """
        Get dictionary of vault names and balances for a user.
        
        Args:
            username: User to get vaults for
            
        Returns:
            Dictionary mapping vault names to balances
        """
        username = self._normalize_username(username)
        user_id = self.get_user_id(username)
        
        self.c.execute(
            "SELECT vault_name, balance FROM vaults WHERE user_id = ?",
            (user_id,)
        )
        vaults = self.c.fetchall()
        return {vault_name: balance for vault_name, balance in vaults}
    
    def get_user_balance(self, username: str) -> float:
        """
        Get total balance across all vaults for a user.
        
        Args:
            username: User to get balance for
            
        Returns:
            Total balance
        """
        username = self._normalize_username(username)
        user_id = self.get_user_id(username)
        
        self.c.execute(
            "SELECT SUM(balance) FROM vaults WHERE user_id = ?",
            (user_id,)
        )
        result = self.c.fetchone()
        return result[0] if result[0] is not None else 0.0
    
    # ==================== TRANSACTION OPERATIONS ====================
    
    def add_transaction(
        self,
        username: str,
        vault_name: str,
        transaction_type: str,
        money_amount: float,
        category: str,
        description: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        date: Optional[str] = None
    ) -> bool:
        """
        Add a transaction to the database.
        
        Args:
            username: User making the transaction
            vault_name: Vault for the transaction
            transaction_type: Type of transaction (Deposit, Withdraw, Transfer, Loan)
            money_amount: Amount of money
            category: Transaction category
            description: Transaction description
            quantity: Optional quantity
            unit: Optional unit
            date: Optional date (defaults to now)
            
        Returns:
            True if successful
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        vault_id = self.get_vault_id(username, vault_name)
        category_id = self.get_category_id(category)
        unit_id = self.get_unit_id(unit) if unit else None
        
        self.c.execute(
            '''INSERT INTO transactions
            (vault_id, transaction_type, amount, category_id, description, quantity, unit_id, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (vault_id, transaction_type, money_amount, category_id,
            description.lower(), quantity, unit_id, date)
        )
        self.conn.commit()
        return True
    
    # ==================== CATEGORY OPERATIONS ====================
    
    def get_category_id(self, category: str) -> int:
        """
        Get category ID for a category name.
        
        Args:
            category: Category name
            
        Returns:
            Category ID
            
        Raises:
            ValueError: If category doesn't exist
        """
        self.c.execute(
            "SELECT category_id FROM categories WHERE category_name = ?",
            (category,)
        )
        result = self.c.fetchone()
        if result is None:
            raise ValueError(f"Category '{category}' does not exist")
        return result[0]
    
    def get_category_names(self) -> List[str]:
        """
        Get list of all category names.
        
        Returns:
            List of category names
        """
        self.c.execute("SELECT category_name FROM categories")
        categories = self.c.fetchall()
        return [category[0] for category in categories]
    
    # ==================== UNIT OPERATIONS ====================
    
    def get_unit_id(self, unit_name: Optional[str]) -> Optional[int]:
        """
        Get unit ID for a unit name.
        
        Args:
            unit_name: Unit name (can be None)
            
        Returns:
            Unit ID or None if unit_name is None
            
        Raises:
            ValueError: If unit doesn't exist
        """
        if unit_name is None:
            return None
        
        self.c.execute(
            "SELECT unit_id FROM units WHERE unit_name = ?",
            (unit_name,)
        )
        result = self.c.fetchone()
        if result is None:
            raise ValueError(f"Unit '{unit_name}' does not exist")
        return result[0]
    
    def get_unit_names(self) -> List[str]:
        """
        Get list of all unit names.
        
        Returns:
            List of unit names
        """
        self.c.execute("SELECT unit_name FROM units")
        units = self.c.fetchall()
        return [unit[0] for unit in units]
    
    # ==================== LOAN OPERATIONS ====================
    
    def add_loan(
        self,
        from_user: str,
        from_vault: str,
        to_user: str,
        to_vault: str,
        money_amount: float
    ) -> None:
        """
        Add or update a loan record.
        
        Args:
            from_user: User lending money
            from_vault: Vault money is coming from
            to_user: User receiving money
            to_vault: Vault money is going to
            money_amount: Amount of the loan
        """
        from_vault_id = self.get_vault_id(from_user, from_vault)
        to_vault_id = self.get_vault_id(to_user, to_vault)
        
        # Check if loan already exists
        self.c.execute(
            "SELECT 1 FROM loans WHERE from_vault_id = ? AND to_vault_id = ?",
            (from_vault_id, to_vault_id)
        )
        
        if self.c.fetchone():
            # Update existing loan
            self.c.execute(
                """UPDATE loans 
                SET amount = amount + ?
                WHERE from_vault_id = ? AND to_vault_id = ?""",
                (money_amount, from_vault_id, to_vault_id)
            )
        else:
            # Create new loan
            self.c.execute(
                "INSERT INTO loans (from_vault_id, to_vault_id, amount) VALUES (?, ?, ?)",
                (from_vault_id, to_vault_id, money_amount)
            )
        
        self.conn.commit()
    
    def get_loans(self, username: str) -> List[Tuple[str, str, float]]:
        """
        Get all loans involving a user.
        
        Args:
            username: User to get loans for
            
        Returns:
            List of tuples (from_user, to_user, total_amount)
        """
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
        return self.c.fetchall()
    
    # ==================== HIGH-LEVEL TRANSACTION METHODS ====================
    
    def deposit(
        self,
        username: str,
        vault_name: str,
        amount: float,
        category_name: str,
        description: str,
        date: Optional[str] = None
    ) -> bool:
        """
        Process a deposit transaction.
        
        Args:
            username: User making the deposit
            vault_name: Vault to deposit into
            amount: Amount to deposit
            category_name: Transaction category
            description: Transaction description
            date: Optional date
            
        Returns:
            True if successful
        """
        self.add_to_vault(username, vault_name, amount)
        self.add_transaction(
            username, vault_name, "Deposit", float(amount),
            category_name, description, date=date
        )
        return True
    
    def withdraw(
        self,
        username: str,
        vault_name: str,
        amount: float,
        category_name: str,
        description: str,
        on_insufficient_funds: Callable[[], None],
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        date: Optional[str] = None
    ) -> bool:
        """
        Process a withdrawal transaction.
        
        Args:
            username: User making the withdrawal
            vault_name: Vault to withdraw from
            amount: Amount to withdraw
            category_name: Transaction category
            description: Transaction description
            on_insufficient_funds: Callback for insufficient funds
            quantity: Optional quantity
            unit: Optional unit
            date: Optional date
            
        Returns:
            True if successful, False if insufficient funds
        """
        try:
            self.remove_from_vault(username, vault_name, amount, on_insufficient_funds)
            self.add_transaction(
                username, vault_name, "Withdraw", -float(amount),
                category_name, description, quantity, unit, date
            )
            return True
        except InsufficientFundsError:
            return False
    
    def transfer(
        self,
        from_user: str,
        from_vault: str,
        to_user: str,
        to_vault: str,
        amount: float,
        on_insufficient_funds: Callable[[], None],
        description: Optional[str] = None,
        is_loan_: bool = False
    ) -> bool:
        """
        Process a transfer between vaults.
        
        Args:
            from_user: User sending money
            from_vault: Source vault
            to_user: User receiving money
            to_vault: Destination vault
            amount: Amount to transfer
            on_insufficient_funds: Callback for insufficient funds
            description: Optional description
            is_loan_: Whether this is a loan
            
        Returns:
            True if successful, False if insufficient funds
        """
        transaction_type = "Loan" if is_loan_ else "Transfer"
        description = description or f"{transaction_type}ing money"
        
        try:
            self.remove_from_vault(from_user, from_vault, amount, on_insufficient_funds)
            self.add_to_vault(to_user, to_vault, amount)
            self.add_transaction(
                from_user, from_vault, transaction_type,
                -float(amount), "Others", description
            )
            self.add_transaction(
                to_user, to_vault, transaction_type,
                float(amount), "Others", description
            )
            return True
        except InsufficientFundsError:
            return False
    
    def loan(
        self,
        from_user: str,
        from_vault: str,
        to_user: str,
        to_vault: str,
        amount: float,
        description: Optional[str] = None
    ) -> bool:
        """
        Process a loan transaction.
        
        Args:
            from_user: User lending money
            from_vault: Source vault
            to_user: User borrowing money
            to_vault: Destination vault
            amount: Loan amount
            description: Optional description
            
        Returns:
            True if successful
        """
        def dummy_callback():
            pass
        
        success = self.transfer(
            from_user, from_vault, to_user, to_vault,
            amount, dummy_callback, description, is_loan_=True
        )
        
        if success:
            self.add_loan(from_user, from_vault, to_user, to_vault, amount)
        
        return success
    
    # ==================== EXPORT OPERATIONS ====================
    
    def export_to_excel(self, username: str) -> None:
        """
        Export user transactions and loans to an Excel file.
        
        Args:
            username: User to export data for
            
        Raises:
            PermissionError: If file is open or write permission denied
        """
        transactions_df = self._get_transactions_dataframe(username)
        loans_df = self._get_loans_dataframe(username)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if file_path:
            with pd.ExcelWriter(file_path) as writer:
                transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
                loans_df.to_excel(writer, sheet_name='Loans', index=False)
            
            print(f"Transactions and loans exported to {file_path}")
    
    def _get_transactions_dataframe(self, username: str) -> pd.DataFrame:
        """
        Get transactions as a pandas DataFrame.
        
        Args:
            username: User to get transactions for
            
        Returns:
            DataFrame of transactions
        """
        query = '''
            SELECT 
                vaults.vault_name,
                transactions.transaction_type,
                transactions.amount,
                categories.category_name,
                transactions.description,
                transactions.quantity,
                units.unit_name,
                transactions.date
            FROM transactions
            LEFT JOIN vaults ON transactions.vault_id = vaults.vault_id
            LEFT JOIN categories ON transactions.category_id = categories.category_id
            LEFT JOIN units ON transactions.unit_id = units.unit_id
            WHERE vaults.user_id = ?
            ORDER BY transactions.date DESC
        '''
        
        self.c.execute(query, (self.get_user_id(username),))
        rows = self.c.fetchall()
        
        return pd.DataFrame(rows, columns=[
            'Vault Name',
            'Transaction Type',
            'Amount',
            'Category Name',
            'Description',
            'Quantity',
            'Unit Name',
            'Date'
        ])
    
    def _get_loans_dataframe(self, username: str) -> pd.DataFrame:
        """
        Get loans as a pandas DataFrame.
        
        Args:
            username: User to get loans for
            
        Returns:
            DataFrame of loans
        """
        loans = self.get_loans(username)
        return pd.DataFrame(
            loans,
            columns=['From User', 'To User', 'Total Loan Amount']
        )