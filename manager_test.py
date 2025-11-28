import pytest #type:ignore
from unittest.mock import Mock
from manager import Manager
from result_types import AuthResult, AuthSuccess, AuthFailure, AuthError, TransactionError, TransactionFailure, TransactionSuccess

@pytest.fixture
def manager():
    mgr = Manager(":memory:")
    mgr.db = Mock()
    return mgr

#LOGIN TESTS
def test_login_success(manager):
    manager.db.user_exists.return_value = True
    manager.db.check_user_password.return_value=True

    result = manager.login("alice","1234")
    assert isinstance(result,AuthSuccess)
    assert result.username == "Alice"

def test_login_invalid_username(manager):
    manager.db.user_exists.return_value = False

    result = manager.login("bob","abcd")

    assert isinstance(result,AuthFailure)
    assert result.error == AuthError.INVALID_USERNAME

def test_login_invalid_password(manager):
    manager.db.user_exists.return_value = True
    manager.db.check_user_password.return_value = False

    result = manager.login("charlie", "passwordISwrong")
    
    assert isinstance(result, AuthFailure)
    assert result.error == AuthError.INVALID_PASSWORD


#SIGNIN TESTS
def test_signup_success(manager):
    manager.db.user_exists.return_value=False
    
    result = manager.signup("robert","pass1234","pass1234")

    assert isinstance(result,AuthSuccess)
    assert result.username=="Robert"

def test_signup_invalid_username_correct_pass(manager):
    manager.db.user_exists.return_value=True

    result = manager.signup("robert","pass1234","pass1234")

    assert isinstance(result,AuthFailure)
    assert result.error==AuthError.USERNAME_EXISTS

def test_signup_invalid_username_wrong_pass(manager):
    manager.db.user_exists.return_value=True

    result = manager.signup("robert","pass1234","pss1234")

    assert isinstance(result,AuthFailure)
    assert result.error==AuthError.USERNAME_EXISTS

def test_signup_password_mismatch(manager):
    manager.db.user_exists.return_value=False

    result = manager.signup("robert","Pass1234","pass1234")

    assert isinstance(result,AuthFailure)
    assert result.error==AuthError.PASSWORD_MISMATCH

#LOGOUT TESTS

def test_logout(manager):
    manager._current_username = "Benson"
    manager.logout()

    assert manager._current_username == ""

#PROCESS_DEPOSIT TESTS

def test_deposit_success(manager):
    result = manager.process_deposit("some_vault",512,"some_category","money from Joe", "2025/01/05")
    assert isinstance(result,TransactionSuccess)
    
def test_deposit_negative_money(manager):
    result = manager.process_deposit("some_vault",-1,"some_category","money from Joe", "2025/01/05")
    assert isinstance(result,TransactionFailure)
    assert result.error == TransactionError.INVALID_AMOUNT
