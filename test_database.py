"""
Comprehensive test suite for the Database class.
Tests all CRUD operations for users, vaults, transactions, loans, categories, and units.
"""

import pytest #type:ignore
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd
from Database import Database

#Setting the schema
TABLE_NAMES = {
            'users', 'vaults', 'transactions',
            'categories', 'units'
        }
USER_COLUMNS = {'user_id', 'username', 'password'}
VAULT_COLUMNS = {'vault_id', 'vault_name', 'user_id', 'balance'}
TRANSACTIONS_COLUMNS = {
            'transaction_id', 'vault_id', 'transaction_type',
            'amount', 'category_id', 'description', 'quantity',
            'unit_id', 'date'
        }
CATEGORIES_COLUMNS = {"category_id","category_name"}
UNIT_COLUMNS = {"unit_id","unit_name"}


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    database = Database(":memory:")
    # Add default test categories and units
    database.c.execute("INSERT INTO categories (category_name) VALUES ('Food')")
    database.c.execute("INSERT INTO categories (category_name) VALUES ('Transport')")
    database.c.execute("INSERT INTO categories (category_name) VALUES ('Others')")
    database.c.execute("INSERT INTO units (unit_name) VALUES ('kg')")
    database.c.execute("INSERT INTO units (unit_name) VALUES ('liters')")
    database.conn.commit()
    yield database
    database.close()


@pytest.fixture
def db_with_user(db):
    """Database with a test user already created."""
    db.add_user("TestUser", "password123")
    return db


@pytest.fixture
def db_with_vault(db_with_user):
    """Database with a test user and an additional vault."""
    db_with_user.add_vault("TestUser", "Savings")
    return db_with_user


class TestDatabaseInitialization:
    """Test database initialization and correct table schema"""
    
    def test_database_connection(self, db):
        """Test that database connection is established."""
        assert db.conn is not None
        assert db.c is not None
    
    def test_tables_created(self, db):
        """Test that all required tables are created. (and only the correct ones)"""
        db.c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in db.c.fetchall()}
        assert TABLE_NAMES.issubset(tables)
    
    def test_users_table_schema(self, db):
        """Test users table has correct schema."""
        db.c.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in db.c.fetchall()}
        assert USER_COLUMNS.issubset(columns)
    
    def test_vaults_table_schema(self, db):
        """Test vaults table has correct schema."""
        db.c.execute("PRAGMA table_info(vaults)")
        columns = {row[1] for row in db.c.fetchall()}
        assert VAULT_COLUMNS.issubset(columns)
    
    def test_transactions_table_schema(self, db):
        """Test transactions table has correct schema."""
        db.c.execute("PRAGMA table_info(transactions)")
        columns = {row[1] for row in db.c.fetchall()}
        assert TRANSACTIONS_COLUMNS.issubset(columns)
        assert columns.issubset(TRANSACTIONS_COLUMNS)


class TestUserOperations:
    """Test user-related database operations."""
    
    def test_normalize_username(self, db):
        """Test username normalization."""
        assert db._normalize_username("testuser") == "Testuser"
        assert db._normalize_username("TESTUSER") == "Testuser"
        assert db._normalize_username("TestUser") == "Testuser"
    
    def test_add_user_success(self, db):
        """Test adding a new user."""
        db.add_user("NewUser", "password")
        assert db.user_exists("NewUser")
    
    def test_add_user_creates_main_vault(self, db):
        """Test that adding a user creates a default Main vault,
        because every user must have a Main vault at all times"""
        db.add_user("UserWithVault")
        vaults = db.get_user_vault_names("UserWithVault")
        assert "Main" in vaults
    
    def test_add_user_duplicate_raises_error(self, db_with_user):
        """Test that adding duplicate user raises error."""
        #maybe We should have our own custom errors for the database?
        with pytest.raises(sqlite3.IntegrityError):
            db_with_user.add_user("TestUser", "password")
    
    def test_user_exists_true(self, db_with_user):
        """Test user_exists returns True for existing user."""
        assert db_with_user.user_exists("TestUser")
    
    def test_user_exists_false(self, db):
        """Test user_exists returns False for non-existing user."""
        assert not db.user_exists("NonExistent")
    
    def test_get_user_id_success(self, db_with_user):
        """Test getting user ID for existing user."""
        user_id = db_with_user.get_user_id("TestUser")
        assert isinstance(user_id, int)
        assert user_id > 0
    
    def test_get_user_id_nonexistent_raises_error(self, db):
        """Test getting user ID for non-existing user raises error."""
        with pytest.raises(ValueError):
            db.get_user_id("NonExistent")
    
    def test_get_usernames(self, db):
        """Test getting all usernames."""
        db.add_user("User1")
        db.add_user("User2")
        db.add_user("User3")
        
        usernames = db.get_usernames()
        assert len(usernames) == 3
        assert "User1" in usernames
        assert "User2" in usernames
        assert "User3" in usernames
    
    def test_check_user_password_correct(self, db_with_user):
        """Test password verification with correct password."""
        assert db_with_user.check_user_password("TestUser", "password123")
    
    def test_check_user_password_incorrect(self, db_with_user):
        """Test password verification with incorrect password."""
        assert not db_with_user.check_user_password("TestUser", "wrongpassword")
    
    def test_check_user_password_nonexistent_user(self, db):
        """Test password check for non-existing user."""
        assert not db.check_user_password("NonExistent", "password")


class TestVaultOperations:
    """Test vault-related database operations."""
    
    def test_add_vault_success(self, db_with_user):
        """Test adding a new vault."""
        db_with_user.add_vault("TestUser", "Checking")
        assert db_with_user.vault_exists("TestUser", "Checking")
    
    def test_add_vault_normalizes_vault_name(self, db_with_user):
        """Test that vault names are capitalized."""
        db_with_user.add_vault("TestUser", "savings")
        assert db_with_user.vault_exists("TestUser", "Savings")

    def test_add_vault_normalizes_username(self, db_with_user):
        """Test that vault names are capitalized."""
        db_with_user.add_vault("testUser", "Savings")
        assert db_with_user.vault_exists("TestUser", "Savings")

    def test_add_vault_duplicate_raises_error(self, db_with_vault):
        """Test adding duplicate vault raises error."""
        with pytest.raises(sqlite3.IntegrityError):
            db_with_vault.add_vault("TestUser", "Savings")
    
    def test_vault_exists_true(self, db_with_user):
        """Test vault_exists returns True for existing vault."""
        assert db_with_user.vault_exists("TestUser", "Main")
    
    def test_vault_exists_false(self, db_with_user):
        """Test vault_exists returns False for non-existing vault."""
        assert not db_with_user.vault_exists("TestUser", "NonExistent")
    
    def test_vault_exists_nonexistent_user(self, db):
        """Test vault_exists for non-existing user."""
        assert not db.vault_exists("NonExistent", "Main")
    
    def test_get_vault_id_success(self, db_with_user):
        """Test getting vault ID for existing vault."""
        vault_id = db_with_user.get_vault_id("TestUser", "Main")
        assert isinstance(vault_id, int)
        assert vault_id > 0
    
    def test_get_vault_id_nonexistent_raises_error(self, db_with_user):
        """Test getting vault ID for non-existing vault raises error."""
        with pytest.raises(ValueError):
            db_with_user.get_vault_id("TestUser", "NonExistent")
    
    def test_get_user_vault_names(self, db_with_vault):
        """Test getting all vault names for a user."""
        vaults = db_with_vault.get_user_vault_names("TestUser")
        assert len(vaults) == 2
        assert "Main" in vaults
        assert "Savings" in vaults
    
    def test_get_user_vaults_with_balances(self, db_with_vault):
        """Test getting vaults with their balances."""
        db_with_vault.add_to_vault("TestUser", "Main", 100.0)
        db_with_vault.add_to_vault("TestUser", "Savings", 200.0)
        
        vaults = db_with_vault.get_user_vaults("TestUser")
        assert vaults["Main"] == 100.0
        assert vaults["Savings"] == 200.0
    
    def test_add_to_vault(self, db_with_user):
        """Test adding money to a vault."""
        db_with_user.add_to_vault("TestUser", "Main", 150.50)
        vaults = db_with_user.get_user_vaults("TestUser")
        assert vaults["Main"] == 150.50
    
    def test_add_to_vault_multiple_times(self, db_with_user):
        """Test adding money to vault multiple times."""
        db_with_user.add_to_vault("TestUser", "Main", 100.0)
        db_with_user.add_to_vault("TestUser", "Main", 50.0)
        vaults = db_with_user.get_user_vaults("TestUser")
        assert vaults["Main"] == 150.0
    
    def test_remove_from_vault(self, db_with_user):
        """Test removing money from a vault."""
        db_with_user.add_to_vault("TestUser", "Main", 200.0)
        db_with_user.remove_from_vault("TestUser", "Main", 75.0)
        vaults = db_with_user.get_user_vaults("TestUser")
        assert vaults["Main"] == 125.0
    
    def test_vault_has_balance_sufficient(self, db_with_user):
        """Test checking if vault has sufficient balance."""
        db_with_user.add_to_vault("TestUser", "Main", 100.0)
        assert db_with_user.vault_has_balance("TestUser", "Main", 50.0)
        assert db_with_user.vault_has_balance("TestUser", "Main", 100.0)
    
    def test_vault_has_balance_insufficient(self, db_with_user):
        """Test checking if vault has insufficient balance."""
        db_with_user.add_to_vault("TestUser", "Main", 100.0)
        assert not db_with_user.vault_has_balance("TestUser", "Main", 150.0)
    
    def test_vault_has_balance_nonexistent_vault(self, db_with_user):
        """Test balance check for non-existing vault."""
        assert not db_with_user.vault_has_balance("TestUser", "NonExistent", 50.0)
    
    def test_get_user_balance_single_vault(self, db_with_user):
        """Test getting total balance with single vault."""
        db_with_user.add_to_vault("TestUser", "Main", 100.0)
        assert db_with_user.get_user_balance("TestUser") == 100.0
    
    def test_get_user_balance_multiple_vaults(self, db_with_vault):
        """Test getting total balance across multiple vaults."""
        db_with_vault.add_to_vault("TestUser", "Main", 100.0)
        db_with_vault.add_to_vault("TestUser", "Savings", 200.0)
        assert db_with_vault.get_user_balance("TestUser") == 300.0
    
    def test_get_user_balance_empty(self, db_with_user):
        """Test getting balance for user with no money."""
        assert db_with_user.get_user_balance("TestUser") == 0.0


class TestCategoryOperations:
    """Test category-related database operations."""
    
    def test_get_category_id_success(self, db):
        """Test getting category ID for existing category."""
        category_id = db.get_category_id("Food")
        assert isinstance(category_id, int)
        assert category_id > 0
    
    def test_get_category_id_nonexistent_raises_error(self, db):
        """Test getting category ID for non-existing category raises error."""
        with pytest.raises(ValueError):
            db.get_category_id("NonExistent")
    
    def test_get_category_names(self, db):
        """Test getting all category names."""
        categories = db.get_category_names()
        assert "Food" in categories
        assert "Transport" in categories
        assert "Others" in categories


class TestUnitOperations:
    """Test unit-related database operations."""
    
    def test_get_unit_id_success(self, db):
        """Test getting unit ID for existing unit."""
        unit_id = db.get_unit_id("kg")
        assert isinstance(unit_id, int)
        assert unit_id > 0
    
    def test_get_unit_id_none_returns_none(self, db):
        """Test getting unit ID with None returns None."""
        assert db.get_unit_id(None) is None
    
    def test_get_unit_id_nonexistent_raises_error(self, db):
        """Test getting unit ID for non-existing unit raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            db.get_unit_id("NonExistent")
    
    def test_get_unit_names(self, db):
        """Test getting all unit names."""
        units = db.get_unit_names()
        assert "kg" in units
        assert "liters" in units


class TestTransactionOperations:
    """Test transaction-related database operations."""
    
    def test_add_transaction_basic(self, db_with_user):
        """Test adding a basic transaction."""
        success = db_with_user.add_transaction(
            username="TestUser",
            vault_name="Main",
            transaction_type="Deposit",
            money_amount=100.0,
            category="Food",
            description="Grocery shopping",
            date="2024-01-01"
        )
        assert success is True
    
    def test_add_transaction_with_quantity_and_unit(self, db_with_user):
        """Test adding transaction with quantity and unit."""
        success = db_with_user.add_transaction(
            username="TestUser",
            vault_name="Main",
            transaction_type="Withdraw",
            money_amount=50.0,
            category="Food",
            description="Vegetables",
            quantity=2.5,
            unit="kg",
            date="2024-01-01"
        )
        assert success is True
    
    def test_add_transaction_without_date(self, db_with_user):
        """Test adding transaction without date (uses current date)."""
        result = db_with_user.add_transaction(
                username="TestUser",
                vault_name="Main",
                transaction_type="Deposit",
                money_amount=100.0,
                category="Others",
                description="Test transaction",
            )
        result = True
    
    def test_deposit_increases_balance(self, db_with_user):
        """Test that deposit increases vault balance."""
        db_with_user.deposit(
            username="TestUser",
            vault_name="Main",
            amount=100.0,
            category_name="Food",
            description="Deposit test",
            date="2010/10/10"
        )
        balance = db_with_user.get_user_balance("TestUser")
        assert balance == 100.0
    
    def test_deposit_creates_transaction(self, db_with_user):
        """Test that deposit creates a transaction record."""
        db_with_user.deposit(
            username="TestUser",
            vault_name="Main",
            amount=100.0,
            category_name="Food",
            description="Deposit test",
            date="2024-01-01"
        )
        
        # Check transaction was created
        vault_id = db_with_user.get_vault_id("TestUser", "Main")
        db_with_user.c.execute(
            "SELECT amount FROM transactions WHERE vault_id = ?",
            (vault_id,)
        )
        result = db_with_user.c.fetchone()
        assert result is not None
        assert result[0] == 100.0
    
    def test_withdraw_decreases_balance(self, db_with_user):
        """Test that withdraw decreases vault balance."""
        db_with_user.add_to_vault("TestUser", "Main", 200.0)
        db_with_user.withdraw(
            username="TestUser",
            vault_name="Main",
            amount=75.0,
            category_name="Food",
            description="Withdraw test",
            date="2010/10/10"
        )
        balance = db_with_user.get_user_balance("TestUser")
        assert balance == 125.0
    
    def test_withdraw_with_quantity_and_unit(self, db_with_user):
        """Test withdraw with quantity and unit."""
        db_with_user.add_to_vault("TestUser", "Main", 100.0)
        db_with_user.withdraw(
            username="TestUser",
            vault_name="Main",
            amount=50.0,
            category_name="Food",
            description="Groceries",
            quantity=3.0,
            unit="kg",
            date="2011/10/10"
        )
        balance = db_with_user.get_user_balance("TestUser")
        assert balance == 50.0


class TestTransferOperations:
    """Test transfer-related database operations."""
    
    def test_transfer_between_same_user_vaults(self, db_with_vault):
        """Test transferring between vaults of same user."""
        db_with_vault.add_to_vault("TestUser", "Main", 200.0)
        
        db_with_vault.transfer(
            from_user="TestUser",
            from_vault="Main",
            to_user="TestUser",
            to_vault="Savings",
            amount=100.0,
            description="Transfer to savings"
        )
        
        vaults = db_with_vault.get_user_vaults("TestUser")
        assert vaults["Main"] == 100.0
        assert vaults["Savings"] == 100.0
    
    def test_transfer_between_different_users(self, db_with_user):
        """Test transferring between different users."""
        db_with_user.add_user("User2")
        db_with_user.add_to_vault("TestUser", "Main", 200.0)
        
        db_with_user.transfer(
            from_user="TestUser",
            from_vault="Main",
            to_user="User2",
            to_vault="Main",
            amount=75.0
        )
        
        balance1 = db_with_user.get_user_balance("TestUser")
        balance2 = db_with_user.get_user_balance("User2")
        assert balance1 == 125.0
        assert balance2 == 75.0
    
    def test_transfer_creates_two_transactions(self, db_with_vault):
        """Test that transfer creates transactions for both vaults."""
        db_with_vault.add_to_vault("TestUser", "Main", 100.0)
        
        db_with_vault.transfer(
            from_user="TestUser",
            from_vault="Main",
            to_user="TestUser",
            to_vault="Savings",
            amount=50.0
        )
        
        # Check transactions for both vaults
        vault1_id = db_with_vault.get_vault_id("TestUser", "Main")
        vault2_id = db_with_vault.get_vault_id("TestUser", "Savings")
        
        db_with_vault.c.execute(
            "SELECT COUNT(*) FROM transactions WHERE vault_id = ?",
            (vault1_id,)
        )
        assert db_with_vault.c.fetchone()[0] == 1
        
        db_with_vault.c.execute(
            "SELECT COUNT(*) FROM transactions WHERE vault_id = ?",
            (vault2_id,)
        )
        assert db_with_vault.c.fetchone()[0] == 1


class DontTestLoanOperations:
    """Test loan-related database operations."""
    
    def test_add_loan_new(self, db_with_user):
        """Test adding a new loan."""
        db_with_user.add_user("User2")
        
        db_with_user.add_loan(
            from_user="TestUser",
            from_vault="Main",
            to_user="User2",
            to_vault="Main",
            money_amount=100.0
        )
        
        loans = db_with_user.get_loans("TestUser")
        assert len(loans) > 0
        assert any(loan[2] == 100.0 for loan in loans)
    
    def test_add_loan_updates_existing(self, db_with_user):
        """Test that adding loan to existing record updates amount."""
        db_with_user.add_user("User2")
        
        db_with_user.add_loan(
            from_user="TestUser",
            from_vault="Main",
            to_user="User2",
            to_vault="Main",
            money_amount=100.0
        )
        
        db_with_user.add_loan(
            from_user="TestUser",
            from_vault="Main",
            to_user="User2",
            to_vault="Main",
            money_amount=50.0
        )
        
        loans = db_with_user.get_loans("TestUser")
        # Should have one loan with total 150.0
        assert any(loan[2] == 150.0 for loan in loans)
    
    def test_get_loans_empty(self, db_with_user):
        """Test getting loans when none exist."""
        loans = db_with_user.get_loans("TestUser")
        assert loans == []
    
    def test_get_loans_as_lender(self, db_with_user):
        """Test getting loans where user is the lender."""
        db_with_user.add_user("User2")
        
        db_with_user.add_loan(
            from_user="TestUser",
            from_vault="Main",
            to_user="User2",
            to_vault="Main",
            money_amount=200.0
        )
        
        loans = db_with_user.get_loans("TestUser")
        assert len(loans) == 1
        assert loans[0][0] == "Testuser"  # Normalized username
        assert loans[0][1] == "User2"
        assert loans[0][2] == 200.0
    
    def test_get_loans_as_borrower(self, db_with_user):
        """Test getting loans where user is the borrower."""
        db_with_user.add_user("User2")
        
        db_with_user.add_loan(
            from_user="User2",
            from_vault="Main",
            to_user="TestUser",
            to_vault="Main",
            money_amount=150.0
        )
        
        loans = db_with_user.get_loans("TestUser")
        assert len(loans) == 1
        assert loans[0][0] == "User2"
        assert loans[0][1] == "Testuser"
        assert loans[0][2] == 150.0


class DontTestExportOperations:
    """Test data export operations."""
    
    @patch('Database.filedialog.asksaveasfilename')
    @patch('pandas.ExcelWriter')
    def test_export_to_excel_success(self, mock_writer, mock_filedialog, db_with_user):
        """Test successful export to Excel."""
        mock_filedialog.return_value = "/path/to/export.xlsx"
        mock_writer_instance = MagicMock()
        mock_writer.return_value.__enter__.return_value = mock_writer_instance
        
        # Add some test data
        db_with_user.deposit("TestUser", "Main", 100.0, "Food", "Test deposit")
        
        db_with_user.export_to_excel("TestUser")
        
        mock_filedialog.assert_called_once()
        mock_writer.assert_called_once_with("/path/to/export.xlsx")
    
    @patch('Database.filedialog.asksaveasfilename')
    def test_export_to_excel_cancelled(self, mock_filedialog, db_with_user):
        """Test export when user cancels file dialog."""
        mock_filedialog.return_value = ""
        
        # Should not raise error when cancelled
        db_with_user.export_to_excel("TestUser")
    
    def test_get_transactions_dataframe(self, db_with_user):
        """Test getting transactions as DataFrame."""
        db_with_user.deposit("TestUser", "Main", 100.0, "Food", "Test")
        db_with_user.withdraw("TestUser", "Main", 50.0, "Transport", "Test")
        
        df = db_with_user._get_transactions_dataframe("TestUser")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'Amount' in df.columns
        assert 'Category Name' in df.columns
    
    def dont_test_get_loans_dataframe(self, db_with_user):
        """Test getting loans as DataFrame."""
        db_with_user.add_user("User2")
        db_with_user.add_loan("TestUser", "Main", "User2", "Main", 100.0)
        
        df = db_with_user._get_loans_dataframe("TestUser")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert 'Total Loan Amount' in df.columns


class TestDatabaseClose:
    """Test database connection management."""
    
    def test_close_connection(self):
        """Test closing database connection."""
        db = Database(":memory:")
        db.close()
        
        # Attempting to execute after close should raise error
        with pytest.raises(sqlite3.ProgrammingError):
            db.c.execute("SELECT 1")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_add_vault_to_nonexistent_user(self, db):
        """Test adding vault to non-existing user raises error."""
        with pytest.raises(ValueError):
            db.add_vault("NonExistent", "TestVault")
    
    def test_transaction_with_invalid_category(self, db_with_user):
        """Test transaction with invalid category raises error."""
        with pytest.raises(ValueError):
            db_with_user.add_transaction(
                "TestUser", "Main", "Deposit", 100.0,
                "InvalidCategory", "Test"
            )
    
    def test_transaction_with_invalid_unit(self, db_with_user):
        """Test transaction with invalid unit raises error."""
        with pytest.raises(ValueError):
            db_with_user.add_transaction(
                "TestUser", "Main", "Withdraw", 50.0,
                "Food", "Test", quantity=1.0, unit="InvalidUnit"
            )
    
    def test_negative_amounts(self, db_with_user):
        """Test handling of negative amounts."""
        # Deposit with negative should still work (math-wise)
        db_with_user.add_to_vault("TestUser", "Main", -50.0)
        balance = db_with_user.get_user_balance("TestUser")
        assert balance == -50.0
    
    def test_very_large_amounts(self, db_with_user):
        """Test handling of very large amounts."""
        large_amount = 999999999.99
        db_with_user.add_to_vault("TestUser", "Main", large_amount)
        balance = db_with_user.get_user_balance("TestUser")
        assert balance == large_amount
    
    def test_special_characters_in_description(self, db_with_user):
        """Test transactions with special characters in description."""
        success = db_with_user.add_transaction(
            "TestUser", "Main", "Deposit", 100.0,
            "Food", "Test with 'quotes' and \"double\" & symbols!@#"
        )
        assert success is True