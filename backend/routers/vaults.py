"""backend/routers/vaults.py — Vault CRUD"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from typing import Dict

from backend.auth import get_current_user
from backend.db import Database
from backend.deps import get_db

router = APIRouter(prefix="/vaults", tags=["vaults"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class VaultOut(BaseModel):
    name: str
    balance: float


class VaultsResponse(BaseModel):
    vaults: list[VaultOut]
    total_balance: float


class CreateVaultRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Vault name cannot be empty")
        return v


class RenameVaultRequest(BaseModel):
    new_name: str

    @field_validator("new_name")
    @classmethod
    def new_name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("New name cannot be empty")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=VaultsResponse)
def list_vaults(
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    vaults_dict: Dict[str, float] = db.get_user_vaults(username)
    vaults = [VaultOut(name=k, balance=v) for k, v in vaults_dict.items()]
    total = sum(v.balance for v in vaults)
    return VaultsResponse(vaults=vaults, total_balance=round(total, 2))


@router.post("", response_model=VaultOut, status_code=status.HTTP_201_CREATED)
def create_vault(
    body: CreateVaultRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    name = body.name.strip().capitalize()
    if db.vault_exists(username, name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vault '{name}' already exists"
        )
    db.add_vault(username, name)
    return VaultOut(name=name, balance=0.0)


@router.get("/{vault_name}", response_model=VaultOut)
def get_vault(
    vault_name: str,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    if not db.vault_exists(username, vault_name):
        raise HTTPException(status_code=404, detail=f"Vault '{vault_name}' not found")
    vaults = db.get_user_vaults(username)
    return VaultOut(name=vault_name, balance=vaults[vault_name])


@router.patch("/{vault_name}/rename")
def rename_vault(
    vault_name: str,
    body: RenameVaultRequest,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    if not db.vault_exists(username, vault_name):
        raise HTTPException(status_code=404, detail=f"Vault '{vault_name}' not found")
    new_name = body.new_name.strip().capitalize()
    if db.vault_exists(username, new_name):
        raise HTTPException(
            status_code=409,
            detail=f"A vault named '{new_name}' already exists"
        )
    db.rename_vault(username, vault_name, new_name)
    return {"message": f"Renamed '{vault_name}' → '{new_name}'"}


@router.delete("/{vault_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vault(
    vault_name: str,
    db: Database = Depends(get_db),
    username: str = Depends(get_current_user),
):
    if not db.vault_exists(username, vault_name):
        raise HTTPException(status_code=404, detail=f"Vault '{vault_name}' not found")
    deleted = db.delete_vault(username, vault_name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a vault with a non-zero balance. Transfer or withdraw all funds first."
        )
