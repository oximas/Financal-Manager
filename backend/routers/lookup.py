"""backend/routers/lookup.py — Categories, Units, Settings, Summary/Dashboard"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.db import Database
from backend.deps import get_db

router = APIRouter(tags=["lookup"])


# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

categories_router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryRequest(BaseModel):
    name: str


@categories_router.get("", response_model=List[str])
def list_categories(
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    return db.get_category_names(username)


@categories_router.post("", status_code=status.HTTP_201_CREATED)
def add_category(
    body: CategoryRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Category name cannot be empty")
    db.add_category(name, username)
    return {"message": f"Category '{name}' added"}


@categories_router.delete("/{category_name}")
def delete_category(
    category_name: str,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    deleted = db.delete_category(category_name, username)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found or is a system category (cannot delete)"
        )
    return {"message": f"Category '{category_name}' deleted"}


# ══════════════════════════════════════════════════════════════════════════════
#  UNITS
# ══════════════════════════════════════════════════════════════════════════════

units_router = APIRouter(prefix="/units", tags=["units"])


class UnitRequest(BaseModel):
    name: str


@units_router.get("", response_model=List[str])
def list_units(
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    return db.get_unit_names(username)


@units_router.post("", status_code=status.HTTP_201_CREATED)
def add_unit(
    body: UnitRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Unit name cannot be empty")
    db.add_unit(name, username)
    return {"message": f"Unit '{name}' added"}


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

settings_router = APIRouter(prefix="/settings", tags=["settings"])

SUPPORTED_CURRENCIES = [
    "EGP", "USD", "EUR", "GBP", "SAR", "AED", "KWD", "QAR", "JOD", "TRY"
]


class SettingsOut(BaseModel):
    currency: str
    supported_currencies: List[str]


class UpdateSettingsRequest(BaseModel):
    currency: str


@settings_router.get("", response_model=SettingsOut)
def get_settings(
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    s = db.get_settings(username)
    return SettingsOut(currency=s["currency"], supported_currencies=SUPPORTED_CURRENCIES)


@settings_router.put("")
def update_settings(
    body: UpdateSettingsRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    currency = body.currency.upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported currency '{currency}'. Supported: {SUPPORTED_CURRENCIES}"
        )
    db.update_settings(username, currency)
    return {"message": f"Currency updated to {currency}"}


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY / DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

summary_router = APIRouter(prefix="/summary", tags=["summary"])


@summary_router.get("/monthly")
def monthly_summary(
    year: int = Query(default=None),
    month: int = Query(default=None),
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    return db.get_monthly_summary(username, year, month)


@summary_router.get("/spending-by-category")
def spending_by_category(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    return db.get_spending_by_category(username, date_from, date_to)


@summary_router.get("/total-balance")
def total_balance(
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    balance = db.get_user_balance(username)
    vaults = db.get_user_vaults(username)
    currency = db.get_settings(username)["currency"]
    return {
        "total_balance": round(balance, 2),
        "currency": currency,
        "vault_count": len(vaults),
    }
