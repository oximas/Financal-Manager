# core/bulk_processor.py
"""
Bulk transaction processing and validation.
Handles validation of multiple transactions and calculates running balances.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class BulkTransactionError(Enum):
    """Error types for bulk transactions"""
    EMPTY_BATCH = "empty_batch"
    INVALID_AMOUNT = "invalid_amount"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_VAULT = "invalid_vault"
    INVALID_CATEGORY = "invalid_category"
    INVALID_UNIT = "invalid_unit"
    INVALID_DATE = "invalid_date"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    SAME_VAULT_TRANSFER = "same_vault_transfer"
    INVALID_USER = "invalid_user"


@dataclass
class ValidationError:
    """Represents a validation error for a specific row"""
    row_number: int
    field: str
    error_type: BulkTransactionError
    message: str


@dataclass
class BulkValidationResult:
    """Result of bulk transaction validation"""
    is_valid: bool
    errors: List[ValidationError]
    valid_count: int
    total_count: int
    
    @property
    def error_summary(self) -> str:
        """Get human-readable error summary"""
        if self.is_valid:
            return f"All {self.total_count} transactions are valid"
        return f"Found {len(self.errors)} errors in {self.total_count} transactions"


@dataclass
class TransactionRow:
    """Represents a single transaction row"""
    row_number: int
    transaction_type: str
    vault: str
    amount: Optional[float]
    category: Optional[str]
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    to_user: Optional[str] = None
    to_vault: Optional[str] = None
    date: Optional[str] = None
    
    def is_empty(self) -> bool:
        """Check if row is completely empty"""
        return (
            not self.transaction_type and
            not self.vault and
            self.amount is None and
            not self.category and
            not self.description
        )


class BulkTransactionValidator:
    """Validates bulk transactions with running balance calculation"""
    
    def __init__(self, db_interface):
        """
        Initialize validator.
        
        Args:
            db_interface: Database interface with methods:
                - get_user_vaults(username) -> Dict[str, float]
                - vault_exists(username, vault_name) -> bool
                - get_category_names() -> List[str]
                - get_unit_names() -> List[str]
                - user_exists(username) -> bool
        """
        self.db = db_interface
        self.current_username: str = ""
    
    def validate_batch(
        self,
        rows: List[TransactionRow],
        current_username: str
    ) -> BulkValidationResult:
        """
        Validate a batch of transactions with running balance.
        
        Args:
            rows: List of transaction rows to validate
            current_username: Current logged-in user
            
        Returns:
            BulkValidationResult with validation status and errors
        """
        self.current_username = current_username
        errors: List[ValidationError] = []
        
        # Filter out completely empty rows
        non_empty_rows = [row for row in rows if not row.is_empty()]
        
        if not non_empty_rows:
            errors.append(ValidationError(
                row_number=0,
                field="batch",
                error_type=BulkTransactionError.EMPTY_BATCH,
                message="No transactions to process"
            ))
            return BulkValidationResult(
                is_valid=False,
                errors=errors,
                valid_count=0,
                total_count=0
            )
        
        # Get current vault balances
        running_balances = self.db.get_user_vaults(current_username).copy()
        
        # Validate each row
        for row in non_empty_rows:
            row_errors = self._validate_row(row, running_balances)
            errors.extend(row_errors)
            
            # Update running balances if row is valid
            if not row_errors:
                self._update_running_balance(row, running_balances)
        
        return BulkValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            valid_count=len(non_empty_rows) - len(set(e.row_number for e in errors)),
            total_count=len(non_empty_rows)
        )
    
    def _validate_row(
        self,
        row: TransactionRow,
        running_balances: Dict[str, float]
    ) -> List[ValidationError]:
        """Validate a single transaction row"""
        errors: List[ValidationError] = []
        
        # Validate transaction type
        if not row.transaction_type:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="transaction_type",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Transaction type is required"
            ))
            return errors  # Can't validate further without type
        
        # Common validations
        errors.extend(self._validate_common_fields(row))
        
        # Type-specific validations
        if row.transaction_type.lower() == "deposit":
            errors.extend(self._validate_deposit(row))
        elif row.transaction_type.lower() == "withdraw":
            errors.extend(self._validate_withdraw(row, running_balances))
        elif row.transaction_type.lower() == "transfer":
            errors.extend(self._validate_transfer(row, running_balances))
        
        return errors
    
    def _validate_common_fields(self, row: TransactionRow) -> List[ValidationError]:
        """Validate fields common to all transaction types"""
        errors: List[ValidationError] = []
        
        # Validate vault
        if not row.vault:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="vault",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Vault is required"
            ))
        elif not self.db.vault_exists(self.current_username, row.vault):
            errors.append(ValidationError(
                row_number=row.row_number,
                field="vault",
                error_type=BulkTransactionError.INVALID_VAULT,
                message=f"Vault '{row.vault}' does not exist"
            ))
        
        # Validate amount
        if row.amount is None:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="amount",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Amount is required"
            ))
        elif row.amount <= 0:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="amount",
                error_type=BulkTransactionError.INVALID_AMOUNT,
                message="Amount must be positive"
            ))
        
        # Validate description
        if not row.description:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="description",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Description is required"
            ))
        
        # Validate date if provided
        if row.date:
            try:
                datetime.strptime(row.date, "%Y-%m-%d")
            except ValueError:
                errors.append(ValidationError(
                    row_number=row.row_number,
                    field="date",
                    error_type=BulkTransactionError.INVALID_DATE,
                    message="Date must be in YYYY-MM-DD format"
                ))
        
        return errors
    
    def _validate_deposit(self, row: TransactionRow) -> List[ValidationError]:
        """Validate deposit-specific fields"""
        errors: List[ValidationError] = []
        
        # Validate category
        if not row.category:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="category",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Category is required"
            ))
        elif row.category not in self.db.get_category_names():
            errors.append(ValidationError(
                row_number=row.row_number,
                field="category",
                error_type=BulkTransactionError.INVALID_CATEGORY,
                message=f"Category '{row.category}' does not exist"
            ))
        
        return errors
    
    def _validate_withdraw(
        self,
        row: TransactionRow,
        running_balances: Dict[str, float]
    ) -> List[ValidationError]:
        """Validate withdraw-specific fields"""
        errors: List[ValidationError] = []
        
        # Validate category
        if not row.category:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="category",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Category is required"
            ))
        elif row.category not in self.db.get_category_names():
            errors.append(ValidationError(
                row_number=row.row_number,
                field="category",
                error_type=BulkTransactionError.INVALID_CATEGORY,
                message=f"Category '{row.category}' does not exist"
            ))
        
        # Validate unit if quantity provided
        if row.quantity is not None and row.quantity > 0:
            if not row.unit:
                errors.append(ValidationError(
                    row_number=row.row_number,
                    field="unit",
                    error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                    message="Unit is required when quantity is specified"
                ))
            elif row.unit not in self.db.get_unit_names():
                errors.append(ValidationError(
                    row_number=row.row_number,
                    field="unit",
                    error_type=BulkTransactionError.INVALID_UNIT,
                    message=f"Unit '{row.unit}' does not exist"
                ))
        
        # Validate sufficient funds (with running balance)
        if row.vault and row.amount:
            current_balance = running_balances.get(row.vault, 0.0)
            if current_balance < row.amount:
                errors.append(ValidationError(
                    row_number=row.row_number,
                    field="amount",
                    error_type=BulkTransactionError.INSUFFICIENT_FUNDS,
                    message=f"Insufficient funds. Balance: {current_balance:.2f}, Required: {row.amount:.2f}"
                ))
        
        return errors
    
    def _validate_transfer(
        self,
        row: TransactionRow,
        running_balances: Dict[str, float]
    ) -> List[ValidationError]:
        """Validate transfer-specific fields"""
        errors: List[ValidationError] = []
        
        # Validate to_user
        if not row.to_user:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="to_user",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Destination user is required"
            ))
        elif not self.db.user_exists(row.to_user):
            errors.append(ValidationError(
                row_number=row.row_number,
                field="to_user",
                error_type=BulkTransactionError.INVALID_USER,
                message=f"User '{row.to_user}' does not exist"
            ))
        
        # Validate to_vault
        if not row.to_vault:
            errors.append(ValidationError(
                row_number=row.row_number,
                field="to_vault",
                error_type=BulkTransactionError.MISSING_REQUIRED_FIELD,
                message="Destination vault is required"
            ))
        elif row.to_user and not self.db.vault_exists(row.to_user, row.to_vault):
            errors.append(ValidationError(
                row_number=row.row_number,
                field="to_vault",
                error_type=BulkTransactionError.INVALID_VAULT,
                message=f"Vault '{row.to_vault}' does not exist for user '{row.to_user}'"
            ))
        
        # Check same vault transfer
        if (row.vault == row.to_vault and 
            row.to_user == self.current_username):
            errors.append(ValidationError(
                row_number=row.row_number,
                field="to_vault",
                error_type=BulkTransactionError.SAME_VAULT_TRANSFER,
                message="Cannot transfer to the same vault"
            ))
        
        # Validate sufficient funds
        if row.vault and row.amount:
            current_balance = running_balances.get(row.vault, 0.0)
            if current_balance < row.amount:
                errors.append(ValidationError(
                    row_number=row.row_number,
                    field="amount",
                    error_type=BulkTransactionError.INSUFFICIENT_FUNDS,
                    message=f"Insufficient funds. Balance: {current_balance:.2f}, Required: {row.amount:.2f}"
                ))
        
        return errors
    
    def _update_running_balance(
        self,
        row: TransactionRow,
        running_balances: Dict[str, float]
    ) -> None:
        """Update running balances after a valid transaction"""
        if not row.vault or row.amount is None:
            return
        
        tx_type = row.transaction_type.lower()
        
        if tx_type == "deposit":
            running_balances[row.vault] = running_balances.get(row.vault, 0.0) + row.amount
        elif tx_type == "withdraw":
            running_balances[row.vault] = running_balances.get(row.vault, 0.0) - row.amount
        elif tx_type == "transfer":
            # Deduct from source vault
            running_balances[row.vault] = running_balances.get(row.vault, 0.0) - row.amount
            # Note: We don't track destination vault balance if it's another user


class BulkTransactionProcessor:
    """Processes validated bulk transactions"""
    
    def __init__(self, manager):
        """
        Initialize processor.
        
        Args:
            manager: Manager instance with transaction processing methods
        """
        self.manager = manager
    
    def process_batch(self, rows: List[TransactionRow]) -> Tuple[int, int]:
        """
        Process a batch of validated transactions.
        
        Args:
            rows: List of validated transaction rows
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for row in rows:
            if row.is_empty():
                continue
            
            try:
                result = self._process_single_transaction(row)
                if result:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Error processing row {row.row_number}: {e}")
                failed += 1
        
        return successful, failed
    
    def _process_single_transaction(self, row: TransactionRow) -> bool:
        """Process a single transaction"""
        tx_type = row.transaction_type.lower()
        
        # Prepare date
        date = row.date
        if date:
            date = date + " " + datetime.now().strftime("%H:%M:%S")
        
        if tx_type == "deposit":
            result = self.manager.process_deposit(
                vault=row.vault,
                amount=row.amount,
                category=row.category,
                description=row.description,
                date=date
            )
        elif tx_type == "withdraw":
            result = self.manager.process_withdraw(
                vault=row.vault,
                amount=row.amount,
                category=row.category,
                description=row.description,
                quantity=row.quantity,
                unit=row.unit,
                date=date
            )
        elif tx_type == "transfer":
            result = self.manager.process_transfer(
                from_vault=row.vault,
                to_user=row.to_user,
                to_vault=row.to_vault,
                amount=row.amount,
                reason=row.description,
                date=date
            )
        else:
            return False
        
        # Check if transaction was successful
        from core.result_types import TransactionSuccess
        return isinstance(result, TransactionSuccess)