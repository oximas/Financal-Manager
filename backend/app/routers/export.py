"""
backend/app/routers/export.py
─────────────────────────────
CSV export endpoint — scoped to the current user, with optional date range.
GET /api/v1/export/csv?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
"""
import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app import models

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/csv")
def export_csv(
    date_from:    Optional[str] = Query(None, description="Start date YYYY-MM-DD (inclusive)"),
    date_to:      Optional[str] = Query(None, description="End date YYYY-MM-DD (inclusive)"),
    db:           Session       = Depends(get_db),
    current_user: models.User   = Depends(get_current_user),
):
    """
    Stream all transactions for the current user as a CSV file.
    Optionally filter by date_from / date_to (both inclusive).
    Pass neither to export everything.
    """
    # ── Collect vault IDs that belong to this user ────────────────────────────
    vault_ids = [
        v.vault_id
        for v in db.query(models.Vault.vault_id).filter(
            models.Vault.user_id == current_user.user_id
        )
    ]

    if not vault_ids:
        # Return an empty CSV with just headers — no error, just nothing there
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=_FIELDS)
        writer.writeheader()
        buf.seek(0)
        return _stream(buf, current_user.username)

    # ── Query transactions ────────────────────────────────────────────────────
    q = (
        db.query(models.Transaction)
        .filter(models.Transaction.vault_id.in_(vault_ids))
        .order_by(models.Transaction.date.asc())
    )

    if date_from:
        q = q.filter(models.Transaction.date >= date_from)
    if date_to:
        # Include the full last day
        q = q.filter(models.Transaction.date <= date_to + " 23:59:59")

    transactions = q.all()

    # ── Build CSV ─────────────────────────────────────────────────────────────
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_FIELDS)
    writer.writeheader()

    for tx in transactions:
        writer.writerow({
            "transaction_id":        tx.transaction_id,
            "date":                  str(tx.date)[:19],   # trim microseconds if any
            "transaction_type":      tx.transaction_type,
            "vault_name":            tx.vault.vault_name if tx.vault else "",
            "amount":                tx.amount,
            "category":              tx.category.category_name if tx.category else "",
            "description":           tx.description,
            "comment":               tx.comment or "",
            "quantity":              tx.quantity if tx.quantity is not None else "",
            "unit":                  tx.unit.unit_name if tx.unit else "",
            "location":              tx.location or "",
            "linked_transaction_id": tx.linked_transaction_id if tx.linked_transaction_id is not None else "",
        })

    buf.seek(0)
    return _stream(buf, current_user.username)


# ── Helpers ───────────────────────────────────────────────────────────────────

_FIELDS = [
    "transaction_id",
    "date",
    "transaction_type",
    "vault_name",
    "amount",
    "category",
    "description",
    "comment",
    "quantity",
    "unit",
    "location",
    "linked_transaction_id",
]


def _stream(buf: io.StringIO, username: str) -> StreamingResponse:
    fname = f"transactions_{username}_{datetime.now():%Y%m%d}.csv"
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8-sig")),  # utf-8-sig = Excel-friendly BOM
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
