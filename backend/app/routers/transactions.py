from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas, services

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=dict)
def list_transactions(
    vault_name:       Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    category:         Optional[str] = Query(None),
    date_from:        Optional[str] = Query(None),
    date_to:          Optional[str] = Query(None),
    search:           Optional[str] = Query(None),
    limit:            int           = Query(100, ge=1, le=500),
    offset:           int           = Query(0, ge=0),
    db:               Session       = Depends(get_db),
    current_user:     models.User   = Depends(get_current_user),
):
    txs, total = services.get_transactions(
        db, current_user,
        vault_name=vault_name,
        transaction_type=transaction_type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "limit": limit, "offset": offset, "transactions": txs}


@router.post("/deposit", response_model=schemas.TransactionResponse, status_code=201)
def deposit(
    payload:      schemas.DepositRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    tx = services.process_deposit(
        db, current_user,
        vault_name=payload.vault_name,
        amount=payload.amount,
        category_name=payload.category,
        description=payload.description,
        comment=payload.comment,
        location=payload.location,
        date=payload.date,
    )
    return services._build_transaction_response(tx)


@router.post("/withdraw", response_model=schemas.TransactionResponse, status_code=201)
def withdraw(
    payload:      schemas.WithdrawRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    tx = services.process_withdraw(
        db, current_user,
        vault_name=payload.vault_name,
        amount=payload.amount,
        category_name=payload.category,
        description=payload.description,
        comment=payload.comment,
        quantity=payload.quantity,
        unit_name=payload.unit,
        location=payload.location,
        date=payload.date,
    )
    return services._build_transaction_response(tx)


@router.post("/transfer", response_model=dict, status_code=201)
def transfer(
    payload:      schemas.TransferRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    from_tx, to_tx = services.process_transfer(
        db, current_user,
        from_vault_name=payload.from_vault,
        to_username=payload.to_username,
        to_vault_name=payload.to_vault,
        amount=payload.amount,
        description=payload.description,
        comment=payload.comment,
        date=payload.date,
    )
    return {
        "from_transaction": services._build_transaction_response(from_tx),
        "to_transaction":   services._build_transaction_response(to_tx),
    }


@router.patch("/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(
    transaction_id: int,
    payload:        schemas.TransactionUpdateRequest,
    db:             Session      = Depends(get_db),
    current_user:   models.User  = Depends(get_current_user),
):
    tx = services.update_transaction(
        db, current_user, transaction_id,
        description=payload.description,
        comment=payload.comment,
    )
    return services._build_transaction_response(tx)


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db:             Session      = Depends(get_db),
    current_user:   models.User  = Depends(get_current_user),
):
    services.delete_transaction(db, current_user, transaction_id)


# ─── Tag assignment on transactions ──────────────────────────────────────────

@router.post("/{transaction_id}/tags/{tag_id}", response_model=schemas.TransactionResponse)
def add_tag_to_transaction(
    transaction_id: int,
    tag_id:         int,
    db:             Session      = Depends(get_db),
    current_user:   models.User  = Depends(get_current_user),
):
    tx = services.add_tag_to_transaction(db, current_user, transaction_id, tag_id)
    return services._build_transaction_response(tx)


@router.delete("/{transaction_id}/tags/{tag_id}", response_model=schemas.TransactionResponse)
def remove_tag_from_transaction(
    transaction_id: int,
    tag_id:         int,
    db:             Session      = Depends(get_db),
    current_user:   models.User  = Depends(get_current_user),
):
    tx = services.remove_tag_from_transaction(db, current_user, transaction_id, tag_id)
    return services._build_transaction_response(tx)

