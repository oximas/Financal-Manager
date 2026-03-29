"""
Pydantic schemas for request validation and response serialization.
Organized by domain: Auth, User, Vault, Transaction, Bulk, Category, Unit, Settings.
"""
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    user_id: int
    username: str

    model_config = {"from_attributes": True}


# ─── Vault ────────────────────────────────────────────────────────────────────

class VaultCreate(BaseModel):
    vault_name: str

    @field_validator("vault_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Vault name cannot be empty")
        return v.capitalize()

class VaultResponse(BaseModel):
    vault_id:   int
    vault_name: str
    balance:    float
    currency:   Optional[str] = None  # None = inherits user setting

    model_config = {"from_attributes": True}


# ─── Category ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    category_name: str

class CategoryResponse(BaseModel):
    category_id:   int
    category_name: str

    model_config = {"from_attributes": True}


# ─── Unit ─────────────────────────────────────────────────────────────────────

class UnitCreate(BaseModel):
    unit_name: str

class UnitResponse(BaseModel):
    unit_id:   int
    unit_name: str

    model_config = {"from_attributes": True}


class RenameRequest(BaseModel):
    """Generic rename payload used for category/unit/tag rename endpoints."""
    name: str


# ─── Tags ─────────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    tag_name: str

class TagResponse(BaseModel):
    tag_id:   int
    tag_name: str

    model_config = {"from_attributes": True}


# ─── Transactions ─────────────────────────────────────────────────────────────

class TransactionResponse(BaseModel):
    transaction_id:        int
    vault_id:              int
    vault_name:            str
    transaction_type:      str
    amount:                float
    category_id:           Optional[int]
    category_name:         Optional[str]
    description:           str
    comment:               Optional[str]
    quantity:              Optional[float]
    unit_id:               Optional[int]
    unit_name:             Optional[str]
    date:                  str
    linked_transaction_id: Optional[int]
    location:              Optional[str]    # Phase 3.5 — advanced/optional
    is_recurring:          bool             # Phase 3.5 — ML-use, hidden from UI
    tags:                  List["TagResponse"] = []  # Phase 3.5

    model_config = {"from_attributes": True}


class DepositRequest(BaseModel):
    vault_name:   str
    amount:       float
    category:     str
    description:  str
    comment:      Optional[str] = None
    location:     Optional[str] = None   # advanced/optional
    date:         Optional[str] = None  # YYYY-MM-DD or YYYY-MM-DD HH:MM:SS

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                datetime.strptime(v, fmt)
                return v
            except ValueError:
                continue
        raise ValueError("Date must be YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")


class WithdrawRequest(BaseModel):
    vault_name:  str
    amount:      float
    category:    str
    description: str
    comment:     Optional[str]  = None
    quantity:    Optional[float] = None
    unit:        Optional[str]  = None
    location:    Optional[str]  = None   # advanced/optional
    date:        Optional[str]  = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                datetime.strptime(v, fmt)
                return v
            except ValueError:
                continue
        raise ValueError("Date must be YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")


class TransferRequest(BaseModel):
    from_vault:  str
    to_username: str
    to_vault:    str
    amount:      float
    description: Optional[str] = None
    comment:     Optional[str] = None
    date:        Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class TransactionUpdateRequest(BaseModel):
    """Allows editing comment and description only (amounts/dates are immutable for integrity)."""
    description: Optional[str] = None
    comment:     Optional[str] = None


class TransactionFilters(BaseModel):
    vault_name:       Optional[str]  = None
    transaction_type: Optional[str]  = None
    category:         Optional[str]  = None
    date_from:        Optional[str]  = None
    date_to:          Optional[str]  = None
    search:           Optional[str]  = None   # searches description + comment
    limit:            int = 100
    offset:           int = 0


# ─── Bulk Transactions ────────────────────────────────────────────────────────

class BulkTransactionRow(BaseModel):
    row_number:       int
    transaction_type: str
    vault_name:       str
    amount:           float
    category:         Optional[str]  = None
    description:      str            = ""
    comment:          Optional[str]  = None
    quantity:         Optional[float] = None
    unit:             Optional[str]  = None
    to_username:      Optional[str]  = None
    to_vault:         Optional[str]  = None
    date:             Optional[str]  = None
    location:         Optional[str]  = None          # Phase 3.5 — advanced
    tag_ids:          Optional[List[int]] = None     # Phase 3.5 — advanced

class BulkValidateRequest(BaseModel):
    rows: List[BulkTransactionRow]

class BulkValidationError(BaseModel):
    row_number: int
    field:      str
    error_type: str
    message:    str

class BulkValidationResponse(BaseModel):
    is_valid:    bool
    errors:      List[BulkValidationError]
    valid_count: int
    total_count: int
    summary:     str

class BulkSubmitRequest(BaseModel):
    rows: List[BulkTransactionRow]

class BulkSubmitResponse(BaseModel):
    successful: int
    failed:     int
    errors:     List[str]


# ─── Settings ─────────────────────────────────────────────────────────────────

class SettingResponse(BaseModel):
    key:   str
    value: str

    model_config = {"from_attributes": True}

class SettingUpdate(BaseModel):
    value: str


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    total_balance:       float
    vaults:              List[VaultResponse]
    recent_transactions: List[TransactionResponse]
    monthly_summary:     dict   # {income, expenses, net} for current month
