# manager.py
"""Business logic layer for the Finance Manager application"""
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from data.database import Database as DB
from core.result_types import *


class TransactionType(Enum):
    """Types of transactions"""
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    LOAN = "loan"

    def __str__(self):
        return self.value


class Manager:
    """
    Manages business logic for the finance application.
    Handles user sessions, authentication, and transaction processing.
    """
    
    def __init__(self, db_file: str):
        self.db = DB(db_file)
        self._current_username: str = ""
    
    # Authentication Methods
    
    def login(self, username: str, password: str) -> AuthResult:
        """
        Attempt to log in a user.
        
        Args:
            username: The username to login with
            password: The password to check
            
        Returns:
            AuthSuccess or AuthFailure
        """
        username = username.capitalize()
        
        if not self.db.user_exists(username):
            return AuthFailure(
                error=AuthError.INVALID_USERNAME,
                message=f"Username '{username}' doesn't exist"
            )
        
        if not self.db.check_user_password(username, password):
            return AuthFailure(
                error=AuthError.INVALID_PASSWORD,
                message="Incorrect password"
            )
        
        self._current_username = username
        return AuthSuccess(username=username)
    
    def signup(self, username: str, password: str, confirm_password: str) -> AuthResult:
        """
        Create a new user account.
        
        Args:
            username: The desired username
            password: The password
            confirm_password: Password confirmation
            
        Returns:
            AuthSuccess or AuthFailure
        """
        username = username.capitalize()
        if self.db.user_exists(username):
            return AuthFailure(
                error=AuthError.USERNAME_EXISTS,
                message=f"Username '{username}' already exists"
            )
        
        if password != confirm_password:
            return AuthFailure(
                error=AuthError.PASSWORD_MISMATCH,
                message="Passwords must match"
            )
        
        try:
            self.db.add_user(username, password)
            self._current_username = username
            return AuthSuccess(username=username)
        except Exception as e:
            return AuthFailure(
                error=AuthError.INVALID_USERNAME,
                message=f"Failed to create account: {str(e)}"
            )
    
    def logout(self):
        """Log out the current user"""
        self._current_username = ""
    

    def process_deposit(
        self,
        vault: str,
        amount: float,
        category: str,
        description: str,
        date: Optional[str] = None
    ) -> TransactionResult:
        """
        Process a deposit transaction.
        
        Args:
            vault: The vault to deposit into
            amount: The amount to deposit
            category: Transaction category
            description: Transaction description
            date: Optional transaction date
            
        Returns:
            TransactionSuccess or TransactionFailure
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if amount < 0:
            return TransactionFailure(
                error=TransactionError.INVALID_AMOUNT,
                message="Amount must be positive"
            )
        
        self.db.deposit(
            self._current_username,
            vault,
            amount,
            category,
            description,
            date
        )
        
        return TransactionSuccess(
            amount=amount,
            message="Deposit successful"
        )
    
    def process_withdraw(
        self,
        vault: str,
        amount: float,
        category: str,
        description: str,
        quantity: float = 1,
        unit: Optional[str] = None,
        date: Optional[str] = None
    ) -> TransactionResult:
        """
        Process a withdrawal transaction.
        
        Args:
            vault: The vault to withdraw from
            amount: The amount to withdraw
            category: Transaction category
            description: Transaction description
            quantity: Optional quantity
            unit: Optional unit
            date: Optional transaction date
            
        Returns:
            TransactionSuccess or TransactionFailure
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if amount < 0:
            return TransactionFailure(
                error=TransactionError.INVALID_AMOUNT,
                message="Amount must be positive"
            )
        
        # Check if sufficient funds
        if not self.db.vault_has_balance(self._current_username, vault, amount):
            current_balance = self.get_vault_balance(vault)
            return TransactionFailure(
                error=TransactionError.INSUFFICIENT_FUNDS,
                message=f"Insufficient funds. Balance: {current_balance:.2f}, Required: {amount:.2f}"
            )
        
        self.db.withdraw(
            self._current_username,
            vault,
            amount,
            category,
            description,
            quantity,
            unit,
            date
        )
        
        return TransactionSuccess(
            amount=amount,
            message="Withdrawal successful"
        )
    
    def process_transfer(
        self,
        from_vault: str,
        to_user: str,
        to_vault: str,
        amount: float,
        reason: Optional[str] = None,
        date:Optional[str]=None
    ) -> TransactionResult:
        """
        Process a transfer transaction.
        
        Args:
            from_vault: Source vault
            to_user: Destination user
            to_vault: Destination vault
            amount: Amount to transfer
            reason: Optional reason for transfer
            
        Returns:
            TransactionSuccess or TransactionFailure
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if amount < 0:
            return TransactionFailure(
                error=TransactionError.INVALID_AMOUNT,
                message="Amount must be positive"
            )
        
        if self.current_username == to_user and from_vault == to_vault:
            return TransactionFailure(
                error=TransactionError.SAME_VAULT_TRANSFER,
                message="Cannot transfer to the same vault"
            )
        
        if not self.db.vault_has_balance(self._current_username, from_vault, amount):
            current_balance = self.get_vault_balance(from_vault)
            return TransactionFailure(
                error=TransactionError.INSUFFICIENT_FUNDS,
                message=f"Insufficient funds. Balance: {current_balance:.2f}, Required: {amount:.2f}"
            )
        
        self.db.transfer(
            self._current_username,
            from_vault,
            to_user,
            to_vault,
            amount,
            reason,
            date
        )
        
        return TransactionSuccess(
            amount=amount,
            message="Transfer successful"
        )

    
    # User Information Methods
    
    @property
    def current_username(self) -> Optional[str]:
        """Get the current logged-in username"""
        return self._current_username
    
    @property
    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in"""
        return bool(self._current_username)
    
    #User Methods
    def get_usernames(self) -> List[str]:
        return self.db.get_usernames()
    
    #Vault Methods
    def get_current_user_vault_names(self) -> List[str]:
        """Get list of vault names for current user"""
        if not self.is_logged_in:
            return []
        return self.db.get_user_vault_names(self._current_username)
    
    def get_current_user_vaults(self) -> Dict[str, float]:
        """Get dictionary of vault names and balances for current user"""
        if not self.is_logged_in:
            return {}
        return self.db.get_user_vaults(self._current_username)
    
    def get_user_vault_names(self,username):
        if not self.is_logged_in:
            return {}
        return self.db.get_user_vault_names(username)
    
    def add_vault_to_current_user(self,vault_name:str):
        if not self.is_logged_in:
            return {}
        self.db.add_vault(self._current_username,vault_name)
    #Balance Methods
    def get_total_balance(self) -> float:
        """Get total balance across all vaults for current user"""
        if not self.is_logged_in:
            return 0.0
        return self.db.get_user_balance(self._current_username)
    
    def get_vault_balance(self, vault_name: str) -> float:
        """Get balance for a specific vault"""
        if not self.is_logged_in:
            return 0.0
        vaults = self.get_current_user_vaults()
        return vaults.get(vault_name, 0.0)
    
    #Category Methods
    def get_category_names(self) -> List[str]:
        return self.db.get_category_names()
    
    #Category Methods
    def get_unit_names(self) -> List[str]:
        return self.db.get_unit_names()
    

    #Exporting and files
    def export_current_user_db_to_excel(self,file_path: str):
        self.db.export_to_excel(self._current_username,file_path)

    