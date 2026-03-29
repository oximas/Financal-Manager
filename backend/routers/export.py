"""backend/routers/export.py — Excel / CSV export"""

import io
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.auth import get_current_user
from backend.db import Database
from backend.deps import get_db

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/excel")
def export_excel(
    vault: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    """Export transactions to Excel file — streams the file directly to the browser."""
    import pandas as pd

    rows = db.get_transactions(
        username, vault_name=vault,
        date_from=date_from, date_to=date_to,
        limit=100_000, offset=0
    )

    df = pd.DataFrame(rows, columns=[
        "transaction_id", "vault_name", "transaction_type", "amount",
        "category_name", "description", "comment", "quantity",
        "unit_name", "date", "linked_transaction_id"
    ])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Transactions", index=False)
    buf.seek(0)

    fname = f"transactions_{username}_{datetime.now():%Y%m%d}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'}
    )


@router.get("/csv")
def export_csv(
    vault: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    """Export transactions to CSV — useful for importing into spreadsheet apps."""
    import csv

    rows = db.get_transactions(
        username, vault_name=vault,
        date_from=date_from, date_to=date_to,
        limit=100_000, offset=0
    )

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "transaction_id", "vault_name", "transaction_type", "amount",
        "category_name", "description", "comment", "quantity",
        "unit_name", "date", "linked_transaction_id"
    ])
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)

    fname = f"transactions_{username}_{datetime.now():%Y%m%d}.csv"
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'}
    )
