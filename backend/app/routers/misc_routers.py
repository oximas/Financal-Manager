from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas, services

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas, services

# ─── Categories ───────────────────────────────────────────────────────────────
categories_router = APIRouter(prefix="/categories", tags=["Categories"])

@categories_router.get("", response_model=List[schemas.CategoryResponse])
def list_categories(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return services.get_categories(db, current_user)

@categories_router.post("", response_model=schemas.CategoryResponse, status_code=201)
def create_category(
    payload:      schemas.CategoryCreate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.create_category(db, current_user, payload.category_name)

@categories_router.patch("/{category_id}", response_model=schemas.CategoryResponse)
def rename_category(
    category_id:  int,
    payload:      schemas.RenameRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.rename_category(db, current_user, category_id, payload.name)

@categories_router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id:  int,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    services.delete_category(db, current_user, category_id)


# ─── Units ────────────────────────────────────────────────────────────────────
units_router = APIRouter(prefix="/units", tags=["Units"])

@units_router.get("", response_model=List[schemas.UnitResponse])
def list_units(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return services.get_units(db, current_user)

@units_router.post("", response_model=schemas.UnitResponse, status_code=201)
def create_unit(
    payload:      schemas.UnitCreate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.create_unit(db, current_user, payload.unit_name)

@units_router.patch("/{unit_id}", response_model=schemas.UnitResponse)
def rename_unit(
    unit_id:      int,
    payload:      schemas.RenameRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.rename_unit(db, current_user, unit_id, payload.name)

@units_router.delete("/{unit_id}", status_code=204)
def delete_unit(
    unit_id:      int,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    services.delete_unit(db, current_user, unit_id)


# ─── Tags ────────────────────────────────────────────────────────────────────
tags_router = APIRouter(prefix="/tags", tags=["Tags"])

@tags_router.get("", response_model=List[schemas.TagResponse])
def list_tags(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return services.get_tags(db, current_user)

@tags_router.post("", response_model=schemas.TagResponse, status_code=201)
def create_tag(
    payload:      schemas.TagCreate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.create_tag(db, current_user, payload.tag_name)

@tags_router.patch("/{tag_id}", response_model=schemas.TagResponse)
def rename_tag(
    tag_id:       int,
    payload:      schemas.RenameRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.rename_tag(db, current_user, tag_id, payload.name)

@tags_router.delete("/{tag_id}", status_code=204)
def delete_tag(
    tag_id:       int,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    services.delete_tag(db, current_user, tag_id)


# ─── Settings ─────────────────────────────────────────────────────────────────
settings_router = APIRouter(prefix="/settings", tags=["Settings"])

@settings_router.get("", response_model=List[schemas.SettingResponse])
def get_settings(
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    settings = services.get_settings(db, current_user)
    return [{"key": s.key, "value": s.value} for s in settings]

@settings_router.put("/{key}", response_model=schemas.SettingResponse)
def update_setting(
    key:          str,
    payload:      schemas.SettingUpdate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    setting = services.upsert_setting(db, current_user, key, payload.value)
    return {"key": setting.key, "value": setting.value}


# ─── Users ───────────────────────────────────────────────────────────────────
users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.User).order_by(models.User.username).all()

@users_router.get("/{username}/vaults", response_model=List[schemas.VaultResponse])
def get_user_vaults_by_name(username: str, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    from fastapi import HTTPException
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found")
    return db.query(models.Vault).filter(models.Vault.user_id == user.user_id).all()

# ─── Dashboard ────────────────────────────────────────────────────────────────
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@dashboard_router.get("", response_model=schemas.DashboardResponse)
def get_dashboard(
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.get_dashboard(db, current_user)


# ─── Analytics ────────────────────────────────────────────────────────────────
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

from datetime import datetime, date as date_type
from sqlalchemy import func, case

@analytics_router.get("")
def get_analytics(
    start_date: Optional[str] = None,
    end_date:   Optional[str] = None,
    db:         Session       = Depends(get_db),
    user:       models.User   = Depends(get_current_user),
):
    # Build date filters
    vault_ids = [v.vault_id for v in db.query(models.Vault.vault_id).filter(models.Vault.user_id == user.user_id)]
    if not vault_ids:
        return {"category_breakdown": [], "monthly": [], "vault_breakdown": [], "balance_history": [], "top_transactions": [], "totals": {}}

    q = db.query(models.Transaction).filter(models.Transaction.vault_id.in_(vault_ids))

    if start_date:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date:
        q = q.filter(models.Transaction.date <= end_date + " 23:59:59")

    txs = q.all()

    # ── Category breakdown (withdrawals only) ─────────────────────────────────
    cat_totals = {}
    for tx in txs:
        if tx.transaction_type == "Withdraw":
            cat = tx.category.category_name if tx.category else "Uncategorized"
            cat_totals[cat] = cat_totals.get(cat, 0) + abs(tx.amount)
    category_breakdown = [
        {"category": k, "amount": round(v, 2)}
        for k, v in sorted(cat_totals.items(), key=lambda x: -x[1])
    ]

    # ── Monthly income vs expenses ────────────────────────────────────────────
    monthly = {}
    for tx in txs:
        try:
            m = str(tx.date)[:7]  # "2025-03"
        except:
            continue
        if m not in monthly:
            monthly[m] = {"month": m, "income": 0, "expenses": 0, "net": 0}
        if tx.transaction_type == "Deposit":
            monthly[m]["income"] += tx.amount
        elif tx.transaction_type == "Withdraw":
            monthly[m]["expenses"] += abs(tx.amount)
    for m in monthly.values():
        m["net"] = round(m["income"] - m["expenses"], 2)
        m["income"] = round(m["income"], 2)
        m["expenses"] = round(m["expenses"], 2)
    monthly_list = sorted(monthly.values(), key=lambda x: x["month"])

    # ── Vault breakdown ────────────────────────────────────────────────────────
    vaults = db.query(models.Vault).filter(models.Vault.user_id == user.user_id).all()
    vault_breakdown = [
        {"vault_name": v.vault_name, "balance": round(v.balance, 2)}
        for v in vaults
    ]

    # ── Balance history (monthly snapshots of total balance) ──────────────────
    # Compute running balance per month across all vaults
    balance_by_month = {}
    all_txs_ordered = db.query(models.Transaction)\
        .filter(models.Transaction.vault_id.in_(vault_ids))\
        .order_by(models.Transaction.date).all()
    running = 0
    for tx in all_txs_ordered:
        try:
            m = str(tx.date)[:7]
        except:
            continue
        if tx.transaction_type in ("Deposit", "Loan"):
            running += tx.amount
        elif tx.transaction_type == "Withdraw":
            running += tx.amount  # already negative
        # Transfer: from_vault - amount, to_vault + amount = net 0 for user total
        balance_by_month[m] = round(running, 2)
    balance_history = [{"month": k, "balance": v} for k, v in sorted(balance_by_month.items())]

    # ── Top 5 biggest withdrawals in period ───────────────────────────────────
    top = sorted([tx for tx in txs if tx.transaction_type == "Withdraw"],
                 key=lambda x: x.amount)[:5]
    top_transactions = [
        {
            "description": tx.description,
            "amount": abs(tx.amount),
            "category": tx.category.category_name if tx.category else "—",
            "date": str(tx.date)[:10],
            "vault": tx.vault.vault_name if tx.vault else "—",
        }
        for tx in top
    ]

    # ── Period totals ──────────────────────────────────────────────────────────
    total_income   = sum(tx.amount for tx in txs if tx.transaction_type == "Deposit")
    total_expenses = sum(abs(tx.amount) for tx in txs if tx.transaction_type == "Withdraw")
    savings_rate   = round((total_income - total_expenses) / total_income * 100, 1) if total_income > 0 else 0

    return {
        "category_breakdown": category_breakdown,
        "monthly":            monthly_list,
        "vault_breakdown":    vault_breakdown,
        "balance_history":    balance_history,
        "top_transactions":   top_transactions,
        "totals": {
            "income":       round(total_income, 2),
            "expenses":     round(total_expenses, 2),
            "net":          round(total_income - total_expenses, 2),
            "savings_rate": savings_rate,
            "tx_count":     len(txs),
        }
    }
