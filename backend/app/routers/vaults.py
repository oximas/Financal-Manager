# backend/app/routers/vaults.py
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas, services
from pydantic import BaseModel

router = APIRouter(prefix="/vaults", tags=["Vaults"])


class RenameVaultRequest(BaseModel):
    new_name: str


class ForceDeleteRequest(BaseModel):
    action: str                         # "withdraw" | "transfer"
    transfer_to: Optional[str] = None
    # ── advanced / optional ──────────────────────────────────────────────────
    # If provided, these override the auto-generated description / comment / date
    # on the drain transaction created before vault deletion.
    description: Optional[str] = None
    comment:     Optional[str] = None
    date:        Optional[str] = None   # YYYY-MM-DD HH:MM:SS


@router.get("", response_model=List[schemas.VaultResponse])
def list_vaults(
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.get_user_vaults(db, current_user)


@router.post("", response_model=schemas.VaultResponse, status_code=201)
def create_vault(
    payload:      schemas.VaultCreate,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.create_vault(db, current_user, payload.vault_name)


@router.patch("/{vault_name}", response_model=schemas.VaultResponse)
def rename_vault(
    vault_name:   str,
    payload:      RenameVaultRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    return services.rename_vault(db, current_user, vault_name, payload.new_name)


@router.delete("/{vault_name}", status_code=204)
def delete_vault(
    vault_name:   str,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    services.delete_vault(db, current_user, vault_name)


@router.post("/{vault_name}/force-delete", status_code=204)
def force_delete_vault(
    vault_name:   str,
    payload:      ForceDeleteRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    services.force_delete_vault(
        db, current_user, vault_name,
        action=payload.action,
        transfer_to=payload.transfer_to,
        description=payload.description,
        comment=payload.comment,
        date=payload.date,
    )
