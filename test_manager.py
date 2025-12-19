import pytest #type:ignore
from unittest.mock import Mock
from manager import Manager, TransactionType
from result_types import (
    AuthResult, AuthSuccess, AuthFailure, AuthError,
    TransactionError, TransactionFailure, TransactionSuccess
)

@pytest.fixture
def manager():
    mgr = Manager(":memory:")
    mgr.db = Mock()
    return mgr


class TestAuthentication:
    """Test authentication-related methods"""
    
    #LOGIN TESTS
    def test_login_success(self, manager):
        """Test successful login"""
        manager.db.user_exists.return_value = True
        manager.db.check_user_password.return_value = True
        
        result = manager.login("john", "password123")
        
        assert isinstance(result, AuthSuccess)
        assert result.username == "John"
        assert manager.current_username == "John"
        manager.db.user_exists.assert_called_once_with("John")
        manager.db.check_user_password.assert_called_once_with("John", "password123")
    
    def test_login_invalid_username(self, manager):
        """Test login with non-existent username"""
        manager.db.user_exists.return_value = False
        
        result = manager.login("nonexistent", "password")
        
        assert isinstance(result, AuthFailure)
        assert result.error == AuthError.INVALID_USERNAME
        assert manager.current_username == ""
        assert result.message != ""
    
    def test_login_invalid_password(self, manager):
        """Test login with incorrect password"""
        manager.db.user_exists.return_value = True
        manager.db.check_user_password.return_value = False
        
        result = manager.login("john", "wrongpassword")
        
        assert isinstance(result, AuthFailure)
        assert result.error == AuthError.INVALID_PASSWORD
        assert manager.current_username == ""
        assert result.message != ""
    
    #SIGNUP TESTS
    def test_signup_success(self, manager):
        """Test successful signup"""
        manager.db.user_exists.return_value = False

        result = manager.signup("newuser", "pass123", "pass123")
        
        assert isinstance(result, AuthSuccess)
        assert result.username == "Newuser"
        assert manager.current_username == "Newuser"
        manager.db.add_user.assert_called_once_with("Newuser", "pass123")
    
    def test_signup_username_exists(self, manager):
        """Test signup with existing username"""
        manager.db.user_exists.return_value = True
        
        result = manager.signup("existing", "pass123", "pass123")
        
        assert isinstance(result, AuthFailure)
        assert result.error == AuthError.USERNAME_EXISTS
        assert manager.current_username == ""
        assert result.message != ""
    
    def test_signup_password_mismatch(self, manager):
        """Test signup with mismatched passwords"""
        manager.db.user_exists.return_value = False
        
        result = manager.signup("newuser", "pass123", "pass456")
        
        assert isinstance(result, AuthFailure)
        assert result.error == AuthError.PASSWORD_MISMATCH
        assert manager.current_username == ""
        assert result.message != ""
    
    def test_signup_database_error(self, manager):
        """Test signup when database fails"""
        manager.db.user_exists.return_value = False
        manager.db.add_user.side_effect = Exception("Database error")
        
        result = manager.signup("newuser", "pass123", "pass123")
        
        assert isinstance(result, AuthFailure)
        assert result.error == AuthError.INVALID_USERNAME
        assert result.message != ""
    
    #LOGOUT TESTS
    def test_logout(self, manager):
        """Test logout functionality"""
        manager._current_username = "John"
        
        manager.logout()
        
        assert manager.current_username == ""
    
    #OTHER AUTH TESTS
    def test_username_capitalization_login(self, manager):
        """Test that usernames are capitalized with login"""
        manager.login("lowercase", "pass")
        manager.db.user_exists.assert_called_with("Lowercase")
    
    def test_username_capitalization_signup(self, manager):
        """Test that usernames are  with signup"""
        manager.signup("lowercase", "pass", "pass")
        manager.db.user_exists.assert_called_with("Lowercase")
    


class TestDeposit:
    """Test deposit transaction methods"""
    
    def test_deposit_success(self, manager):
        """Test successful deposit"""
        manager._current_username = "John"
        manager.db.deposit.return_value = None
        
        result = manager.process_deposit("Savings", 100.0, "Income", "Salary","2025/03/11")
        
        assert isinstance(result, TransactionSuccess)
        assert result.amount == 100.0
        assert "successful" in result.message
        manager.db.deposit.assert_called_once_with(
            "John", "Savings", 100.0, "Income", "Salary", "2025/03/11"
        )
    
    def test_deposit_negative_amount(self, manager):
        """Test deposit with negative amount"""
        manager._current_username = "John"
        
        result = manager.process_deposit("Savings", -50.0, "Income", "Test")
        
        assert isinstance(result, TransactionFailure)
        assert result.error == TransactionError.INVALID_AMOUNT
        assert "positive" in result.message
    
    def test_deposit_with_date(self, manager):
        """Test deposit with custom date"""
        manager._current_username = "John"
        manager.db.deposit.return_value = None
        
        result = manager.process_deposit(
            "Savings", 100.0, "Income", "Salary", date="2025-01-01"
        )
        
        assert isinstance(result, TransactionSuccess)
        manager.db.deposit.assert_called_with(
            "John", "Savings", 100.0, "Income", "Salary", "2025-01-01"
        )


class TestWithdraw:
    """Test withdrawal transaction methods"""
    
    def test_withdraw_success(self, manager):
        """Test successful withdrawal"""
        manager._current_username = "John"
        manager.db.vault_has_balance.return_value = True
        
        result = manager.process_withdraw(
            "Savings", 50.0, "Food", "Groceries"
        )
        
        assert isinstance(result, TransactionSuccess)
        assert result.amount == 50.0
        manager.db.vault_has_balance.assert_called_once_with("John", "Savings", 50.0)
        manager.db.withdraw.assert_called_once()
    
    def test_withdraw_insufficient_funds(self, manager):
        """Test withdrawal with insufficient funds"""
        manager._current_username = "John"
        manager.db.vault_has_balance.return_value = False
        manager.db.get_user_vaults.return_value = {"Savings": 30.0}
        
        result = manager.process_withdraw("Savings", 50.0, "Food", "Groceries")
        
        assert isinstance(result, TransactionFailure)
        assert result.error == TransactionError.INSUFFICIENT_FUNDS
        assert "30.00" in result.message
        assert "50.00" in result.message
    
    def test_withdraw_negative_amount(self, manager):
        """Test withdrawal with negative amount"""
        manager._current_username = "John"
        
        result = manager.process_withdraw("Savings", -20.0, "Food", "Test")
        
        assert isinstance(result, TransactionFailure)
        assert result.error == TransactionError.INVALID_AMOUNT
        assert result.message != ""
    
    def test_withdraw_with_quantity_and_unit(self, manager):
        """Test withdrawal with quantity and unit"""
        manager._current_username = "John"
        manager.db.vault_has_balance.return_value = True
        
        result = manager.process_withdraw(
            "Savings", 30.0, "Food", "Milk", quantity=2.0, unit="liters"
        )
        
        assert isinstance(result, TransactionSuccess)
    
    def test_withdraw_with_date(self, manager):
        """Test withdrawal with custom date"""
        manager._current_username = "John"
        manager.db.vault_has_balance.return_value = True
        
        result = manager.process_withdraw(
            "Savings", 50.0, "Food", "Groceries", date="2025-01-01"
        )
        
        assert isinstance(result, TransactionSuccess)

class TestTransfer:
    """Test transfer transaction methods"""
    
    def test_transfer_success(self, manager):
        """Test successful transfer"""
        manager._current_username = "John"
        manager.db.vault_has_balance.return_value = True
        
        result = manager.process_transfer(
            "Savings", "Jane", "Checking", 100.0, "Gift"
        )
        
        assert isinstance(result, TransactionSuccess)
        assert result.amount == 100.0
        manager.db.transfer.assert_called_once()
    
    def test_transfer_insufficient_funds(self, manager):
        """Test transfer with insufficient funds"""
        manager._current_username = "John"
        manager.db.vault_has_balance.return_value = False
        manager.db.get_user_vaults.return_value = {"Savings": 50.0}
        
        result = manager.process_transfer(
            "Savings", "Jane", "Checking", 100.0
        )
        
        assert isinstance(result, TransactionFailure)
        assert result.error == TransactionError.INSUFFICIENT_FUNDS
        assert result.message != ""
    
    def test_transfer_same_vault(self, manager):
        """Test transfer to same vault"""
        manager._current_username = "John"
        
        result = manager.process_transfer(
            "Savings", "John", "Savings", 50.0
        )
        
        assert isinstance(result, TransactionFailure)
        assert result.error == TransactionError.SAME_VAULT_TRANSFER
        assert result.message != ""
    
    def test_transfer_negative_amount(self, manager):
        """Test transfer with negative amount"""
        manager._current_username = "John"
        
        result = manager.process_transfer(
            "Savings", "Jane", "Checking", -50.0
        )
        
        assert isinstance(result, TransactionFailure)
        assert result.error == TransactionError.INVALID_AMOUNT
        assert result.message != ""
    


class TestUserInformation:
    """Test user information methods"""
    
    def test_current_username_when_logged_in(self, manager):
        """Test getting current username when logged in"""
        manager._current_username = "John"
        
        assert manager.current_username == "John"
    
    def test_current_username_when_logged_out(self, manager):
        """Test getting current username when not logged in"""
        manager._current_username = ""
        
        assert manager.current_username == ""
    
    def test_is_logged_in_true(self, manager):
        """Test is_logged_in when user is logged in"""
        manager._current_username = "John"
        
        assert manager.is_logged_in is True
    
    def test_is_logged_in_false(self, manager):
        """Test is_logged_in when no user is logged in"""
        manager._current_username = ""
        assert manager.is_logged_in is False

        manager._current_username = None
        assert manager.is_logged_in is False


class TestVaultMethods:
    """Test vault-related methods"""
    
    def test_get_current_user_vault_names(self, manager):
        """Test getting vault names for current user"""
        manager._current_username = "John"
        manager.db.get_user_vault_names.return_value = ["Savings", "Checking"]
        
        vaults = manager.get_current_user_vault_names()
        
        assert vaults == ["Savings", "Checking"]
        manager.db.get_user_vault_names.assert_called_once_with("John")
    
    def test_get_current_user_vault_names_not_logged_in(self, manager):
        """Test getting vault names when not logged in"""
        manager._current_username = ""
        
        vaults = manager.get_current_user_vault_names()
        
        assert vaults == []
    
    def test_get_current_user_vaults(self, manager):
        """Test getting vaults with balances for current user"""
        manager._current_username = "John"
        manager.db.get_user_vaults.return_value = {"Savings": 1000.0, "Checking": 500.0}
        
        vaults = manager.get_current_user_vaults()
        
        assert vaults == {"Savings": 1000.0, "Checking": 500.0}
        manager.db.get_user_vaults.assert_called_once_with("John")
    
    def test_get_current_user_vaults_not_logged_in(self, manager):
        """Test getting vaults when not logged in"""
        manager._current_username = ""
        
        vaults = manager.get_current_user_vaults()
        
        assert vaults == {}
    
    def test_add_vault_to_current_user(self, manager):
        """Test adding a vault to current user"""
        manager._current_username = "John"
        
        manager.add_vault_to_current_user("Investment")
        
        manager.db.add_vault.assert_called_once_with("John", "Investment")
    
    def test_add_vault_not_logged_in(self, manager):
        """Test adding vault when not logged in"""
        manager._current_username = ""
        
        result = manager.add_vault_to_current_user("Investment")
        
        assert result == {}


class TestBalanceMethods:
    """Test balance-related methods"""
    
    def test_get_total_balance(self, manager):
        """Test getting total balance"""
        manager._current_username = "John"
        manager.db.get_user_balance.return_value = 1500.0
        
        balance = manager.get_total_balance()
        
        assert balance == 1500.0
        manager.db.get_user_balance.assert_called_once_with("John")
    
    def test_get_total_balance_not_logged_in(self, manager):
        """Test getting total balance when not logged in"""
        manager._current_username = ""
        
        balance = manager.get_total_balance()
        
        assert balance == 0.0
    
    def test_get_vault_balance(self, manager):
        """Test getting balance for specific vault"""
        manager._current_username = "John"
        manager.db.get_user_vaults.return_value = {"Savings": 1000.0, "Checking": 500.0}
        
        balance = manager.get_vault_balance("Savings")
        
        assert balance == 1000.0
    
    def test_get_vault_balance_nonexistent(self, manager):
        """Test getting balance for nonexistent vault"""
        manager._current_username = "John"
        manager.db.get_user_vaults.return_value = {"Savings": 1000.0}
        
        balance = manager.get_vault_balance("Nonexistent")
        
        assert balance == 0.0
    
    def test_get_vault_balance_not_logged_in(self, manager):
        """Test getting vault balance when not logged in"""
        manager._current_username = ""
        
        balance = manager.get_vault_balance("Savings")
        
        assert balance == 0.0


class TestCategoryAndUnitMethods:
    """Test category and unit methods"""
    
    def test_get_category_names(self, manager):
        """Test getting category names"""
        manager.db.get_category_names.return_value = ["Food", "Transport", "Income"]
        
        categories = manager.get_category_names()
        
        assert categories == ["Food", "Transport", "Income"]
        manager.db.get_category_names.assert_called_once()
    
    def test_get_unit_names(self, manager):
        """Test getting unit names"""
        manager.db.get_unit_names.return_value = ["liters", "kg", "items"]
        
        units = manager.get_unit_names()
        
        assert units == ["liters", "kg", "items"]
        manager.db.get_unit_names.assert_called_once()


class TestExportMethods:
    """Test export functionality"""
    
    def test_export_to_excel(self, manager):
        """Test exporting database to Excel"""
        manager._current_username = "John"
        
        manager.export_current_user_db_to_excel()
        
        manager.db.export_to_excel.assert_called_once_with("John")


class TestTransactionType:
    """Test TransactionType enum"""
    
    def test_transaction_type_values(self):
        """Test TransactionType enum values"""
        assert str(TransactionType.WITHDRAW) == "withdraw"
        assert str(TransactionType.DEPOSIT) == "deposit"
        assert str(TransactionType.TRANSFER) == "transfer"
        assert str(TransactionType.LOAN) == "loan"
    
    def test_transaction_type_enum_members(self):
        """Test TransactionType enum members"""
        assert TransactionType.WITHDRAW.value =="withdraw"
        assert TransactionType.DEPOSIT.value == "deposit"
        assert TransactionType.TRANSFER.value == "transfer"
        assert TransactionType.LOAN.value == "loan"