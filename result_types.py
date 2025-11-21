from dataclasses import dataclass
from typing import Optional, Generic, TypeVar
from enum import Enum


T = TypeVar("T")

class ResultStatus(Enum):
    """Status of an operation result"""
    SUCCESS = "success"
    ERROR = "error"

class AuthError(Enum):
    """Authentication error types"""
    INVALID_USERNAME = "invalid_username"
    INVALID_PASSWORD = "invalid_password"
    USERNAME_EXISTS = "username_exists"
    PASSWORD_MISMATCH = "password_mismatch"

class TransactionError(Enum):
    """Transaction error types"""
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_VAULT = "invalid_vault"
    SAME_VAULT_TRANSFER = "same_vault_transfer"
    VALIDATION_ERROR = "validation_error"

@dataclass
class Result(Generic[T]):
    """Generic results type for opetations"""
    status: ResultStatus
    data: Optional[T] = None
    message: Optional[str] = None
    error_type: Optional[Enum] = None

    @classmethod
    def success(cls, data: T=None, message:Optional[str]=None ) -> 'Result[T]':
        """Create a successful result"""
        return cls(status=ResultStatus.SUCCESS,data=data,message=message)

    @classmethod
    def error(cls,message:str, error_type:Optional[Enum]=None) -> 'Result[T]':
        """Create an error result"""
        return cls(status=ResultStatus.ERROR,message=message,error_type=error_type)

    @property
    def is_success(self) ->bool:
        """Check if result is successful"""
        return self.status ==ResultStatus.SUCCESS

    @property
    def is_error(self) ->bool:
        """Check if result is an error"""
        return self.status ==ResultStatus.ERROR

@dataclass
class AuthSuccess:
    """Successful authentication result"""
    username: str


@dataclass
class AuthFailure:
    """Failed authentication result"""
    error: AuthError
    message: str


# Union type for authentication results
AuthResult = AuthSuccess | AuthFailure


@dataclass
class TransactionSuccess:
    """Successful transaction result"""
    amount: float
    message: str = "Transaction successful"


@dataclass
class TransactionFailure:
    """Failed transaction result"""
    error: TransactionError
    message: str


# Union type for transaction results
TransactionResult = TransactionSuccess | TransactionFailure


# Helper functions for type checking
def is_auth_success(result: AuthResult) -> bool:
    """Check if authentication was successful"""
    return isinstance(result, AuthSuccess)


def is_transaction_success(result: TransactionResult) -> bool:
    """Check if transaction was successful"""
    return isinstance(result, TransactionSuccess)
    