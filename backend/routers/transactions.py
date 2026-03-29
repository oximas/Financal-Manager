"""backend/routers/transactions.py — All transaction operations"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.auth import get_current_user
from backend.db import Database
from backend.deps import get_db
from core.bulk_processor import (
    BulkTransactionValidator,
    BulkTransactionProcessor,
    TransactionRow,
)
from core.result_types import TransactionSuccess
from core.manager import Manager
from backend.config import settings

router = APIRouter(prefix="/transactions", tags=["transactions"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    transaction_id: int
    vault_name: str
    transaction_type: str
    amount: float
    category_name: Optional[str]
    description: str
    comment: Optional[str]
    quantity: Optional[float]
    unit_name: Optional[str]
    date: str
    linked_transaction_id: Optional[int]


class PaginatedTransactions(BaseModel):
    transactions: List[TransactionOut]
    total: int
    limit: int
    offset: int


class DepositRequest(BaseModel):
    vault: str
    amount: float
    category: str
    description: str
    date: Optional[str] = None
    comment: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class WithdrawRequest(BaseModel):
    vault: str
    amount: float
    category: str
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    date: Optional[str] = None
    comment: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class TransferRequest(BaseModel):
    from_vault: str
    to_user: str
    to_vault: str
    amount: float
    description: Optional[str] = None
    date: Optional[str] = None
    comment: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class UpdateCommentRequest(BaseModel):
    comment: str


class BulkTransactionRowRequest(BaseModel):
    row_number: int
    transaction_type: str
    vault: str
    amount: Optional[float] = None
    category: Optional[str] = None
    description: str = ""
    quantity: Optional[float] = None
    unit: Optional[str] = None
    to_user: Optional[str] = None
    to_vault: Optional[str] = None
    date: Optional[str] = None
    comment: Optional[str] = None


class BulkSubmitRequest(BaseModel):
    rows: List[BulkTransactionRowRequest]


class BulkValidationErrorOut(BaseModel):
    row_number: int
    field: str
    error_type: str
    message: str


class BulkValidationResponse(BaseModel):
    is_valid: bool
    errors: List[BulkValidationErrorOut]
    valid_count: int
    total_count: int
    error_summary: str


class BulkSubmitResponse(BaseModel):
    successful: int
    failed: int
    message: str


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_manager(username: str, db: Database) -> Manager:
    """Build a Manager instance pre-logged-in as the current user."""
    mgr = Manager(settings.DB_PATH)
    mgr._current_username = username
    # Swap the manager's db for our extended one
    mgr.db = db
    return mgr


def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """Validate and normalise a date string to 'YYYY-MM-DD HH:MM:SS'."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise HTTPException(
        status_code=422,
        detail=f"Invalid date format '{date_str}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedTransactions)
def list_transactions(
    vault: Optional[str] = Query(None),
    type: Optional[str] = Query(None, description="deposit | withdraw | transfer"),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    rows = db.get_transactions(
        username, vault_name=vault, transaction_type=type,
        category=category, search=search,
        date_from=date_from, date_to=date_to,
        limit=limit, offset=offset,
    )
    total = db.count_transactions(
        username, vault_name=vault, transaction_type=type,
        category=category, search=search,
        date_from=date_from, date_to=date_to,
    )
    return PaginatedTransactions(
        transactions=[TransactionOut(**r) for r in rows],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    tx = db.get_transaction_by_id(transaction_id, username)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionOut(**tx)


@router.post("/deposit", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def deposit(
    body: DepositRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    if not db.vault_exists(username, body.vault):
        raise HTTPException(status_code=404, detail=f"Vault '{body.vault}' not found")
    if not db.get_category_names(username).__contains__(body.category) and \
       body.category not in db.get_category_names():
        raise HTTPException(status_code=422, detail=f"Category '{body.category}' not found")

    date = _parse_date(body.date) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.add_to_vault(username, body.vault, body.amount)
    tx_id = db.add_transaction(
        username, body.vault, "Deposit", body.amount,
        body.category, body.description, date=date, comment=body.comment,
    )
    return TransactionOut(**db.get_transaction_by_id(tx_id, username))


@router.post("/withdraw", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def withdraw(
    body: WithdrawRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    if not db.vault_exists(username, body.vault):
        raise HTTPException(status_code=404, detail=f"Vault '{body.vault}' not found")
    if not db.vault_has_balance(username, body.vault, body.amount):
        balance = db.get_user_vaults(username).get(body.vault, 0)
        raise HTTPException(
            status_code=409,
            detail=f"Insufficient funds. Balance: {balance:.2f}, Required: {body.amount:.2f}"
        )

    date = _parse_date(body.date) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.remove_from_vault(username, body.vault, body.amount)
    tx_id = db.add_transaction(
        username, body.vault, "Withdraw", -body.amount,
        body.category, body.description,
        quantity=body.quantity, unit=body.unit,
        date=date, comment=body.comment,
    )
    return TransactionOut(**db.get_transaction_by_id(tx_id, username))


@router.post("/transfer", response_model=dict, status_code=status.HTTP_201_CREATED)
def transfer(
    body: TransferRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    if not db.vault_exists(username, body.from_vault):
        raise HTTPException(status_code=404, detail=f"Source vault '{body.from_vault}' not found")
    if not db.user_exists(body.to_user):
        raise HTTPException(status_code=404, detail=f"User '{body.to_user}' not found")
    if not db.vault_exists(body.to_user, body.to_vault):
        raise HTTPException(
            status_code=404,
            detail=f"Vault '{body.to_vault}' not found for user '{body.to_user}'"
        )
    if username == body.to_user and body.from_vault == body.to_vault:
        raise HTTPException(status_code=422, detail="Cannot transfer to the same vault")
    if not db.vault_has_balance(username, body.from_vault, body.amount):
        balance = db.get_user_vaults(username).get(body.from_vault, 0)
        raise HTTPException(
            status_code=409,
            detail=f"Insufficient funds. Balance: {balance:.2f}, Required: {body.amount:.2f}"
        )

    date = _parse_date(body.date) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.transfer(
        username, body.from_vault,
        body.to_user, body.to_vault,
        body.amount,
        description=body.description,
        date=date,
        comment=body.comment,
    )
    return {"message": "Transfer successful", "amount": body.amount}


@router.patch("/{transaction_id}/comment")
def update_comment(
    transaction_id: int,
    body: UpdateCommentRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    updated = db.update_transaction_comment(transaction_id, body.comment, username)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Comment updated"}


# ── Bulk ──────────────────────────────────────────────────────────────────────

@router.post("/bulk/validate", response_model=BulkValidationResponse)
def bulk_validate(
    body: BulkSubmitRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    rows = [TransactionRow(**r.model_dump()) for r in body.rows]
    validator = BulkTransactionValidator(db)
    result = validator.validate_batch(rows, username)

    return BulkValidationResponse(
        is_valid=result.is_valid,
        errors=[
            BulkValidationErrorOut(
                row_number=e.row_number,
                field=e.field,
                error_type=e.error_type.value,
                message=e.message,
            )
            for e in result.errors
        ],
        valid_count=result.valid_count,
        total_count=result.total_count,
        error_summary=result.error_summary,
    )


@router.post("/bulk/submit", response_model=BulkSubmitResponse, status_code=status.HTTP_201_CREATED)
def bulk_submit(
    body: BulkSubmitRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    rows = [TransactionRow(**r.model_dump()) for r in body.rows]

    # Always validate before processing
    validator = BulkTransactionValidator(db)
    validation = validator.validate_batch(rows, username)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail=f"Validation failed: {validation.error_summary}. Call /bulk/validate first."
        )

    mgr = _get_manager(username, db)
    processor = BulkTransactionProcessor(mgr)
    successful, failed = processor.process_batch(rows)

    return BulkSubmitResponse(
        successful=successful,
        failed=failed,
        message=f"Processed {successful} transaction(s) successfully"
        + (f", {failed} failed" if failed else ""),
    )
