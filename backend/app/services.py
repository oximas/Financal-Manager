"""
Business logic service layer.
Adapted from core/manager.py — same rules, same validations,
but stateless (user passed explicitly) and using SQLAlchemy sessions.
"""
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app import models


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _normalize_date(date: Optional[str]) -> str:
    if not date:
        return _now()
    if len(date) == 10:  # YYYY-MM-DD — add current time
        return date + " " + datetime.now().strftime("%H:%M:%S")
    return date

def _get_vault_or_404(db: Session, user_id: int, vault_name: str) -> models.Vault:
    vault = db.query(models.Vault).filter(
        models.Vault.user_id == user_id,
        models.Vault.vault_name == vault_name
    ).first()
    if not vault:
        raise HTTPException(status_code=404, detail=f"Vault '{vault_name}' not found")
    return vault

def _get_category_or_404(db: Session, user_id: int, category_name: str) -> models.Category:
    cat = db.query(models.Category).filter(
        models.Category.user_id == user_id,
        models.Category.category_name == category_name,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
    return cat

def _get_unit_or_none(db: Session, user_id: int, unit_name: Optional[str]) -> Optional[models.Unit]:
    if not unit_name:
        return None
    unit = db.query(models.Unit).filter(
        models.Unit.user_id == user_id,
        models.Unit.unit_name == unit_name,
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit '{unit_name}' not found")
    return unit


# ─── Vault Services ───────────────────────────────────────────────────────────

def get_user_vaults(db: Session, user: models.User) -> List[models.Vault]:
    return db.query(models.Vault).filter(models.Vault.user_id == user.user_id).all()

def get_user_vault_dict(db: Session, user: models.User) -> Dict[str, float]:
    vaults = get_user_vaults(db, user)
    return {v.vault_name: v.balance for v in vaults}

def create_vault(db: Session, user: models.User, vault_name: str) -> models.Vault:
    vault_name = vault_name.strip().capitalize()
    existing = db.query(models.Vault).filter(
        models.Vault.user_id == user.user_id,
        models.Vault.vault_name == vault_name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Vault '{vault_name}' already exists")
    vault = models.Vault(vault_name=vault_name, user_id=user.user_id, balance=0.0)
    db.add(vault)
    db.commit()
    db.refresh(vault)
    return vault

def delete_vault(db: Session, user: models.User, vault_name: str) -> None:
    vault = _get_vault_or_404(db, user.user_id, vault_name)
    if vault.balance != 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete vault '{vault_name}' — balance is {vault.balance:.2f}. "
                   "Transfer or withdraw all funds first."
        )
    db.delete(vault)
    db.commit()


def rename_vault(db: Session, user: models.User, vault_name: str, new_name: str) -> models.Vault:
    new_name = new_name.strip()
    if not new_name:
        raise HTTPException(status_code=422, detail="Vault name cannot be empty")
    if vault_name.lower() == "main":
        raise HTTPException(status_code=403, detail="Cannot rename the Main vault")
    vault = _get_vault_or_404(db, user.user_id, vault_name)
    conflict = db.query(models.Vault).filter(
        models.Vault.user_id == user.user_id,
        models.Vault.vault_name == new_name,
        models.Vault.vault_id  != vault.vault_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail=f"Vault '{new_name}' already exists")
    vault.vault_name = new_name
    db.commit()
    db.refresh(vault)
    return vault


def force_delete_vault(
    db: Session,
    user: models.User,
    vault_name: str,
    action: str,           # "withdraw" | "transfer"
    transfer_to: str = None,
    description: str = None,   # optional custom description for the drain tx
    comment: str = None,       # optional comment
    date: str = None,          # optional custom date
) -> None:
    """
    Delete a vault even when it has a balance.
    action="withdraw"  → creates a Withdraw transaction draining the balance, then deletes.
    action="transfer"  → transfers balance to transfer_to vault, then deletes.
    Vault named "Main" cannot be deleted.
    If description/comment/date are provided they override the auto-generated values.
    """
    vault = _get_vault_or_404(db, user.user_id, vault_name)

    if vault.vault_name.lower() == "main":
        raise HTTPException(status_code=403, detail="Cannot delete the Main vault")

    if vault.balance != 0:
        if action == "withdraw":
            # Find/create an "Others" category for this user
            cat = db.query(models.Category).filter(
                models.Category.user_id == user.user_id,
                models.Category.category_name == "Others",
            ).first()
            if not cat:
                cat = models.Category(category_name="Others", user_id=user.user_id)
                db.add(cat)
                db.flush()

            amount = abs(vault.balance)
            # If balance is positive, withdraw it. If negative, deposit to zero it out.
            tx_type   = "Withdraw" if vault.balance > 0 else "Deposit"
            tx_amount = vault.balance if vault.balance > 0 else -vault.balance

            tx = models.Transaction(
                vault_id=vault.vault_id,
                transaction_type=tx_type,
                amount=-tx_amount if tx_type == "Withdraw" else tx_amount,
                category_id=cat.category_id,
                description=description or f"Vault deletion — {vault_name}",
                comment=comment or None,
                is_recurring=0,
                date=_normalize_date(date),
            )
            vault.balance = 0.0
            db.add(tx)
            db.flush()

        elif action == "transfer":
            if not transfer_to:
                raise HTTPException(status_code=422, detail="transfer_to is required for transfer action")
            dest = _get_vault_or_404(db, user.user_id, transfer_to)
            if dest.vault_id == vault.vault_id:
                raise HTTPException(status_code=422, detail="Cannot transfer to the same vault")

            cat = db.query(models.Category).filter(
                models.Category.user_id == user.user_id,
                models.Category.category_name == "Others",
            ).first()
            if not cat:
                cat = models.Category(category_name="Others", user_id=user.user_id)
                db.add(cat)
                db.flush()

            amount = vault.balance
            tx_date = _normalize_date(date)
            from_tx = models.Transaction(
                vault_id=vault.vault_id,
                transaction_type="Transfer",
                amount=amount,
                category_id=cat.category_id,
                description=description or f"Vault deletion — transfer to {transfer_to}",
                comment=comment or None,
                is_recurring=0,
                date=tx_date,
            )
            to_tx = models.Transaction(
                vault_id=dest.vault_id,
                transaction_type="Transfer",
                amount=amount,
                category_id=cat.category_id,
                description=description or f"Vault deletion — transfer from {vault_name}",
                comment=comment or None,
                is_recurring=0,
                date=tx_date,
            )
            dest.balance += amount
            vault.balance = 0.0
            db.add(from_tx)
            db.add(to_tx)
            db.flush()
            from_tx.linked_transaction_id = to_tx.transaction_id
            to_tx.linked_transaction_id   = from_tx.transaction_id
            db.flush()
        else:
            raise HTTPException(status_code=422, detail="action must be 'withdraw' or 'transfer'")

    db.delete(vault)
    db.commit()


# ─── Transaction Services ─────────────────────────────────────────────────────

def _build_transaction_response(tx: models.Transaction) -> dict:
    """Convert a Transaction ORM object to a response dict."""
    return {
        "transaction_id":        tx.transaction_id,
        "vault_id":              tx.vault_id,
        "vault_name":            tx.vault.vault_name if tx.vault else "",
        "transaction_type":      tx.transaction_type,
        "amount":                tx.amount,
        "category_id":           tx.category_id,
        "category_name":         tx.category.category_name if tx.category else None,
        "description":           tx.description,
        "comment":               tx.comment,
        "quantity":              tx.quantity,
        "unit_id":               tx.unit_id,
        "unit_name":             tx.unit.unit_name if tx.unit else None,
        "date":                  tx.date,
        "linked_transaction_id": tx.linked_transaction_id,
        "location":              tx.location,
        "is_recurring":          bool(tx.is_recurring),
        "tags":                  [{"tag_id": t.tag_id, "tag_name": t.tag_name} for t in (tx.tags or [])],
    }


def get_transactions(
    db: Session,
    user: models.User,
    vault_name: Optional[str] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[dict], int]:
    """Returns (transactions, total_count) respecting filters."""
    query = (
        db.query(models.Transaction)
        .join(models.Vault)
        .filter(models.Vault.user_id == user.user_id)
    )

    if vault_name:
        query = query.filter(models.Vault.vault_name == vault_name)
    if transaction_type:
        query = query.filter(models.Transaction.transaction_type == transaction_type.capitalize())
    if category:
        query = (
            query.join(models.Category)
            .filter(models.Category.category_name == category)
        )
    if date_from:
        query = query.filter(models.Transaction.date >= date_from)
    if date_to:
        query = query.filter(models.Transaction.date <= date_to + " 23:59:59")
    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            func.lower(models.Transaction.description).like(term) |
            func.lower(models.Transaction.comment).like(term)
        )

    total = query.count()
    transactions = (
        query
        .order_by(models.Transaction.date.desc(), models.Transaction.transaction_id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [_build_transaction_response(tx) for tx in transactions], total


def process_deposit(
    db: Session,
    user: models.User,
    vault_name: str,
    amount: float,
    category_name: str,
    description: str,
    comment: Optional[str] = None,
    location: Optional[str] = None,
    date: Optional[str] = None,
) -> models.Transaction:
    vault    = _get_vault_or_404(db, user.user_id, vault_name)
    category = _get_category_or_404(db, user.user_id, category_name)
    date     = _normalize_date(date)

    vault.balance += amount

    tx = models.Transaction(
        vault_id=vault.vault_id,
        transaction_type="Deposit",
        amount=amount,
        category_id=category.category_id,
        description=description,
        comment=comment,
        location=location,
        is_recurring=0,
        date=date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def process_withdraw(
    db: Session,
    user: models.User,
    vault_name: str,
    amount: float,
    category_name: str,
    description: str,
    comment: Optional[str] = None,
    quantity: Optional[float] = None,
    unit_name: Optional[str] = None,
    location: Optional[str] = None,
    date: Optional[str] = None,
) -> models.Transaction:
    vault    = _get_vault_or_404(db, user.user_id, vault_name)
    category = _get_category_or_404(db, user.user_id, category_name)
    unit     = _get_unit_or_none(db, user.user_id, unit_name)
    date     = _normalize_date(date)

    if vault.balance < amount:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient funds. Balance: {vault.balance:.2f}, Required: {amount:.2f}"
        )

    vault.balance -= amount

    tx = models.Transaction(
        vault_id=vault.vault_id,
        transaction_type="Withdraw",
        amount=-amount,
        category_id=category.category_id,
        description=description,
        comment=comment,
        quantity=quantity,
        unit_id=unit.unit_id if unit else None,
        location=location,
        is_recurring=0,
        date=date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def process_transfer(
    db: Session,
    user: models.User,
    from_vault_name: str,
    to_username: str,
    to_vault_name: str,
    amount: float,
    description: Optional[str] = None,
    comment: Optional[str] = None,
    date: Optional[str] = None,
) -> Tuple[models.Transaction, models.Transaction]:
    """Returns (from_tx, to_tx) — both sides of the transfer."""
    # Validate source
    from_vault = _get_vault_or_404(db, user.user_id, from_vault_name)

    # Same vault guard
    if to_username.capitalize() == user.username and to_vault_name == from_vault_name:
        raise HTTPException(status_code=422, detail="Cannot transfer to the same vault")

    # Validate destination user
    to_user = db.query(models.User).filter(
        models.User.username == to_username.capitalize()
    ).first()
    if not to_user:
        raise HTTPException(status_code=404, detail=f"User '{to_username}' not found")

    to_vault = _get_vault_or_404(db, to_user.user_id, to_vault_name)

    # Funds check
    if from_vault.balance < amount:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient funds. Balance: {from_vault.balance:.2f}, Required: {amount:.2f}"
        )

    date        = _normalize_date(date)
    description = description or "Transfer"

    # Get "Others" category for each user separately (categories are now per-user)
    from_others = db.query(models.Category).filter(
        models.Category.category_name == "Others",
        models.Category.user_id == user.user_id,
    ).first()
    to_others = db.query(models.Category).filter(
        models.Category.category_name == "Others",
        models.Category.user_id == to_user.user_id,
    ).first()
    cat_id_from = from_others.category_id if from_others else None
    cat_id_to   = to_others.category_id if to_others else None

    # Update balances
    from_vault.balance -= amount
    to_vault.balance   += amount

    # Create both transaction rows
    from_tx = models.Transaction(
        vault_id=from_vault.vault_id,
        transaction_type="Transfer",
        amount=amount,
        category_id=cat_id_from,
        description=description,
        comment=comment,
        is_recurring=0,
        date=date,
    )
    to_tx = models.Transaction(
        vault_id=to_vault.vault_id,
        transaction_type="Transfer",
        amount=amount,
        category_id=cat_id_to,
        description=description,
        comment=comment,
        is_recurring=0,
        date=date,
    )
    db.add(from_tx)
    db.add(to_tx)
    db.flush()  # Gets IDs without committing

    # Link them together
    from_tx.linked_transaction_id = to_tx.transaction_id
    to_tx.linked_transaction_id   = from_tx.transaction_id

    db.commit()
    db.refresh(from_tx)
    db.refresh(to_tx)
    return from_tx, to_tx


def update_transaction(
    db: Session,
    user: models.User,
    transaction_id: int,
    description: Optional[str],
    comment: Optional[str],
) -> models.Transaction:
    """Only description and comment are editable post-creation (data integrity)."""
    tx = (
        db.query(models.Transaction)
        .join(models.Vault)
        .filter(
            models.Transaction.transaction_id == transaction_id,
            models.Vault.user_id == user.user_id
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if description is not None:
        tx.description = description
    if comment is not None:
        tx.comment = comment

    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, user: models.User, transaction_id: int) -> None:
    """
    Delete a transaction and reverse its effect on vault balance.
    If it's a transfer, also deletes the linked partner.
    """
    tx = (
        db.query(models.Transaction)
        .join(models.Vault)
        .filter(
            models.Transaction.transaction_id == transaction_id,
            models.Vault.user_id == user.user_id
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Reverse balance effect
    vault = tx.vault
    if tx.transaction_type == "Deposit":
        if vault.balance < tx.amount:
            raise HTTPException(
                status_code=422,
                detail="Cannot delete: reversing this deposit would make vault balance negative"
            )
        vault.balance -= tx.amount
    elif tx.transaction_type == "Withdraw":
        vault.balance += abs(tx.amount)
    elif tx.transaction_type == "Transfer":
        # Reverse source side
        vault.balance += tx.amount
        # Also delete and reverse the linked partner if it exists
        if tx.linked_transaction_id:
            partner = db.query(models.Transaction).get(tx.linked_transaction_id)
            if partner:
                partner.vault.balance -= partner.amount
                # Unlink before delete
                tx.linked_transaction_id = None
                db.flush()
                db.delete(partner)

    db.delete(tx)
    db.commit()


# ─── Dashboard ────────────────────────────────────────────────────────────────

def get_dashboard(db: Session, user: models.User) -> dict:
    vaults        = get_user_vaults(db, user)
    total_balance = sum(v.balance for v in vaults)

    # Recent 10 transactions
    recent_txs, _ = get_transactions(db, user, limit=10)

    # Monthly summary — current month
    now        = datetime.now()
    month_from = now.strftime("%Y-%m-01")
    month_to   = now.strftime("%Y-%m-%d")

    monthly_txs, _ = get_transactions(db, user, date_from=month_from, date_to=month_to, limit=10000)

    income   = sum(t["amount"] for t in monthly_txs if t["transaction_type"] == "Deposit")
    expenses = sum(abs(t["amount"]) for t in monthly_txs if t["transaction_type"] == "Withdraw")

    return {
        "total_balance":       total_balance,
        "vaults":              [{"vault_id": v.vault_id, "vault_name": v.vault_name, "balance": v.balance} for v in vaults],
        "recent_transactions": recent_txs,
        "monthly_summary": {
            "income":   income,
            "expenses": expenses,
            "net":      income - expenses,
        },
    }


# ─── Bulk Processing ──────────────────────────────────────────────────────────

def validate_bulk(
    db: Session,
    user: models.User,
    rows: list,
) -> dict:
    """
    Validates a batch of bulk transaction rows with running balance simulation.
    Mirrors the BulkTransactionValidator logic from core/bulk_processor.py.
    """
    errors = []
    vault_balances = get_user_vault_dict(db, user)
    categories     = {c.category_name for c in db.query(models.Category).filter(models.Category.user_id == user.user_id).all()}
    units          = {u.unit_name for u in db.query(models.Unit).filter(models.Unit.user_id == user.user_id).all()}
    usernames      = {u.username for u in db.query(models.User).all()}
    vault_names    = set(vault_balances.keys())

    non_empty = [r for r in rows if not (
        not r.transaction_type and not r.vault_name and r.amount is None and not r.description
    )]

    if not non_empty:
        return {
            "is_valid": False,
            "errors": [{"row_number": 0, "field": "batch", "error_type": "EMPTY_BATCH", "message": "No transactions provided"}],
            "valid_count": 0,
            "total_count": 0,
            "summary": "No transactions to process",
        }

    running = vault_balances.copy()

    for row in non_empty:
        row_errors = []
        tx_type = (row.transaction_type or "").capitalize()

        # ── Required fields ────────────────────────────────────────────────────
        if not tx_type:
            row_errors.append({"row_number": row.row_number, "field": "transaction_type",
                                "error_type": "MISSING_REQUIRED_FIELD", "message": "Transaction type is required"})
            errors.extend(row_errors)
            continue

        if not row.vault_name:
            row_errors.append({"row_number": row.row_number, "field": "vault_name",
                                "error_type": "MISSING_REQUIRED_FIELD", "message": "Vault is required"})
        elif row.vault_name not in vault_names:
            row_errors.append({"row_number": row.row_number, "field": "vault_name",
                                "error_type": "INVALID_VAULT", "message": f"Vault '{row.vault_name}' does not exist"})

        if row.amount is None:
            row_errors.append({"row_number": row.row_number, "field": "amount",
                                "error_type": "MISSING_REQUIRED_FIELD", "message": "Amount is required"})
        elif row.amount <= 0:
            row_errors.append({"row_number": row.row_number, "field": "amount",
                                "error_type": "INVALID_AMOUNT", "message": "Amount must be positive"})

        if not row.description and tx_type != "Transfer":
            row_errors.append({"row_number": row.row_number, "field": "description",
                                "error_type": "MISSING_REQUIRED_FIELD", "message": "Description is required"})

        # ── Type-specific ──────────────────────────────────────────────────────
        if tx_type in ("Deposit", "Withdraw"):
            if not row.category:
                row_errors.append({"row_number": row.row_number, "field": "category",
                                    "error_type": "MISSING_REQUIRED_FIELD", "message": "Category is required"})
            elif row.category not in categories:
                row_errors.append({"row_number": row.row_number, "field": "category",
                                    "error_type": "INVALID_CATEGORY", "message": f"Category '{row.category}' does not exist"})

        if tx_type == "Withdraw":
            if row.unit and row.unit not in units:
                row_errors.append({"row_number": row.row_number, "field": "unit",
                                    "error_type": "INVALID_UNIT", "message": f"Unit '{row.unit}' does not exist"})
            if not row_errors and row.vault_name and row.amount:
                bal = running.get(row.vault_name, 0.0)
                if bal < row.amount:
                    row_errors.append({"row_number": row.row_number, "field": "amount",
                                        "error_type": "INSUFFICIENT_FUNDS",
                                        "message": f"Insufficient funds. Balance: {bal:.2f}, Required: {row.amount:.2f}"})

        if tx_type == "Transfer":
            if not row.to_username:
                row_errors.append({"row_number": row.row_number, "field": "to_username",
                                    "error_type": "MISSING_REQUIRED_FIELD", "message": "Destination user is required"})
            elif row.to_username.capitalize() not in usernames:
                row_errors.append({"row_number": row.row_number, "field": "to_username",
                                    "error_type": "INVALID_USER", "message": f"User '{row.to_username}' does not exist"})
            if not row.to_vault:
                row_errors.append({"row_number": row.row_number, "field": "to_vault",
                                    "error_type": "MISSING_REQUIRED_FIELD", "message": "Destination vault is required"})
            if not row_errors and row.vault_name and row.amount:
                bal = running.get(row.vault_name, 0.0)
                if bal < row.amount:
                    row_errors.append({"row_number": row.row_number, "field": "amount",
                                        "error_type": "INSUFFICIENT_FUNDS",
                                        "message": f"Insufficient funds. Balance: {bal:.2f}, Required: {row.amount:.2f}"})

        errors.extend(row_errors)

        # Update running balance only if this row is clean
        if not row_errors and row.vault_name and row.amount:
            if tx_type == "Deposit":
                running[row.vault_name] = running.get(row.vault_name, 0.0) + row.amount
            elif tx_type == "Withdraw":
                running[row.vault_name] = running.get(row.vault_name, 0.0) - row.amount
            elif tx_type == "Transfer":
                running[row.vault_name] = running.get(row.vault_name, 0.0) - row.amount

    error_rows  = {e["row_number"] for e in errors}
    valid_count = len(non_empty) - len(error_rows)

    return {
        "is_valid":    len(errors) == 0,
        "errors":      errors,
        "valid_count": valid_count,
        "total_count": len(non_empty),
        "summary":     f"All {len(non_empty)} transactions valid" if not errors
                       else f"{len(errors)} error(s) in {len(non_empty)} transactions",
    }


def submit_bulk(db: Session, user: models.User, rows: list) -> dict:
    """Process validated bulk rows — each one calls the appropriate service function."""
    successful = 0
    failed     = 0
    error_msgs = []

    for row in rows:
        try:
            tx_type = (row.transaction_type or "").capitalize()
            date = row.date + " " + datetime.now().strftime("%H:%M:%S") if (row.date and len(row.date) == 10) else row.date

            tx = None  # will hold the created transaction for tag application

            if tx_type == "Deposit":
                tx = process_deposit(db, user, row.vault_name, row.amount, row.category,
                                     row.description, row.comment,
                                     location=row.location if hasattr(row, 'location') else None,
                                     date=date)
            elif tx_type == "Withdraw":
                tx = process_withdraw(db, user, row.vault_name, row.amount, row.category,
                                      row.description, row.comment, row.quantity, row.unit,
                                      location=row.location if hasattr(row, 'location') else None,
                                      date=date)
            elif tx_type == "Transfer":
                tx, _ = process_transfer(db, user, row.vault_name, row.to_username, row.to_vault,
                                         row.amount, row.description, row.comment, date)
            else:
                raise ValueError(f"Unknown transaction type: {tx_type}")

            # Apply tags (only for Deposit/Withdraw, not Transfer)
            if tx is not None and tx_type != "Transfer":
                tag_ids = getattr(row, 'tag_ids', None) or []
                for tid in tag_ids:
                    tag = db.query(models.Tag).filter(
                        models.Tag.tag_id == tid,
                        models.Tag.user_id == user.user_id,
                    ).first()
                    if tag and tag not in tx.tags:
                        tx.tags.append(tag)
                if tag_ids:
                    db.commit()

            successful += 1
        except Exception as e:
            failed += 1
            error_msgs.append(f"Row {row.row_number}: {str(e)}")

    return {"successful": successful, "failed": failed, "errors": error_msgs}


# ─── Category / Unit Services ─────────────────────────────────────────────────

def get_categories(db: Session, user: models.User) -> List[models.Category]:
    return (
        db.query(models.Category)
        .filter(models.Category.user_id == user.user_id)
        .order_by(models.Category.category_name)
        .all()
    )

def create_category(db: Session, user: models.User, name: str) -> models.Category:
    name = name.strip()
    if db.query(models.Category).filter(
        models.Category.user_id == user.user_id,
        models.Category.category_name == name,
    ).first():
        raise HTTPException(status_code=409, detail=f"Category '{name}' already exists")
    cat = models.Category(category_name=name, user_id=user.user_id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

def rename_category(db: Session, user: models.User, category_id: int, new_name: str) -> models.Category:
    new_name = new_name.strip()
    cat = db.query(models.Category).filter(
        models.Category.category_id == category_id,
        models.Category.user_id == user.user_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    # Check new name doesn't conflict
    conflict = db.query(models.Category).filter(
        models.Category.user_id == user.user_id,
        models.Category.category_name == new_name,
        models.Category.category_id != category_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail=f"Category '{new_name}' already exists")
    cat.category_name = new_name
    db.commit()
    db.refresh(cat)
    return cat

def delete_category(db: Session, user: models.User, category_id: int) -> None:
    cat = db.query(models.Category).filter(
        models.Category.category_id == category_id,
        models.Category.user_id == user.user_id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    # Transactions with this category will have category_id set to NULL (ON DELETE SET NULL)
    db.delete(cat)
    db.commit()

def get_units(db: Session, user: models.User) -> List[models.Unit]:
    return (
        db.query(models.Unit)
        .filter(models.Unit.user_id == user.user_id)
        .order_by(models.Unit.unit_name)
        .all()
    )

def create_unit(db: Session, user: models.User, name: str) -> models.Unit:
    name = name.strip()
    if db.query(models.Unit).filter(
        models.Unit.user_id == user.user_id,
        models.Unit.unit_name == name,
    ).first():
        raise HTTPException(status_code=409, detail=f"Unit '{name}' already exists")
    unit = models.Unit(unit_name=name, user_id=user.user_id)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit

def rename_unit(db: Session, user: models.User, unit_id: int, new_name: str) -> models.Unit:
    new_name = new_name.strip()
    unit = db.query(models.Unit).filter(
        models.Unit.unit_id == unit_id,
        models.Unit.user_id == user.user_id,
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    conflict = db.query(models.Unit).filter(
        models.Unit.user_id == user.user_id,
        models.Unit.unit_name == new_name,
        models.Unit.unit_id != unit_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail=f"Unit '{new_name}' already exists")
    unit.unit_name = new_name
    db.commit()
    db.refresh(unit)
    return unit

def delete_unit(db: Session, user: models.User, unit_id: int) -> None:
    unit = db.query(models.Unit).filter(
        models.Unit.unit_id == unit_id,
        models.Unit.user_id == user.user_id,
    ).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    # Transactions with this unit will have unit_id set to NULL (ON DELETE SET NULL)
    db.delete(unit)
    db.commit()


# ─── Settings Services ────────────────────────────────────────────────────────

def get_settings(db: Session, user: models.User) -> List[models.Setting]:
    return db.query(models.Setting).filter(models.Setting.user_id == user.user_id).all()

def get_setting(db: Session, user: models.User, key: str) -> Optional[models.Setting]:
    return db.query(models.Setting).filter(
        models.Setting.user_id == user.user_id,
        models.Setting.key == key
    ).first()

def upsert_setting(db: Session, user: models.User, key: str, value: str) -> models.Setting:
    setting = get_setting(db, user, key)
    if setting:
        setting.value = value
    else:
        setting = models.Setting(user_id=user.user_id, key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


# ─── Tag Services ─────────────────────────────────────────────────────────────

def get_tags(db: Session, user: models.User) -> List[models.Tag]:
    return (
        db.query(models.Tag)
        .filter(models.Tag.user_id == user.user_id)
        .order_by(models.Tag.tag_name)
        .all()
    )

def create_tag(db: Session, user: models.User, name: str) -> models.Tag:
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Tag name cannot be empty")
    if db.query(models.Tag).filter(
        models.Tag.user_id == user.user_id,
        models.Tag.tag_name == name,
    ).first():
        raise HTTPException(status_code=409, detail=f"Tag '{name}' already exists")
    tag = models.Tag(tag_name=name, user_id=user.user_id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

def rename_tag(db: Session, user: models.User, tag_id: int, new_name: str) -> models.Tag:
    new_name = new_name.strip()
    tag = db.query(models.Tag).filter(
        models.Tag.tag_id == tag_id,
        models.Tag.user_id == user.user_id,
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    conflict = db.query(models.Tag).filter(
        models.Tag.user_id == user.user_id,
        models.Tag.tag_name == new_name,
        models.Tag.tag_id != tag_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail=f"Tag '{new_name}' already exists")
    tag.tag_name = new_name
    db.commit()
    db.refresh(tag)
    return tag

def delete_tag(db: Session, user: models.User, tag_id: int) -> None:
    tag = db.query(models.Tag).filter(
        models.Tag.tag_id == tag_id,
        models.Tag.user_id == user.user_id,
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    # transaction_tags rows deleted via CASCADE
    db.delete(tag)
    db.commit()

def add_tag_to_transaction(
    db: Session, user: models.User, transaction_id: int, tag_id: int
) -> models.Transaction:
    """Add a tag to a transaction. Both must belong to this user."""
    tx = (
        db.query(models.Transaction)
        .join(models.Vault)
        .filter(
            models.Transaction.transaction_id == transaction_id,
            models.Vault.user_id == user.user_id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tag = db.query(models.Tag).filter(
        models.Tag.tag_id == tag_id,
        models.Tag.user_id == user.user_id,
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag not in tx.tags:
        tx.tags.append(tag)
        db.commit()
    db.refresh(tx)
    return tx

def remove_tag_from_transaction(
    db: Session, user: models.User, transaction_id: int, tag_id: int
) -> models.Transaction:
    """Remove a tag from a transaction."""
    tx = (
        db.query(models.Transaction)
        .join(models.Vault)
        .filter(
            models.Transaction.transaction_id == transaction_id,
            models.Vault.user_id == user.user_id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tag = db.query(models.Tag).filter(
        models.Tag.tag_id == tag_id,
        models.Tag.user_id == user.user_id,
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag in tx.tags:
        tx.tags.remove(tag)
        db.commit()
    db.refresh(tx)
    return tx

