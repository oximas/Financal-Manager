"""
SQLAlchemy ORM models — mirrors the pfm_v2 schema.
Categories and Units are now per-user (user_id FK added in migration 0001).
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Float, Text, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id:  Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(255))  # bcrypt hash

    # Relationships
    vaults:     Mapped[List["Vault"]]    = relationship(back_populates="user", cascade="all, delete-orphan")
    settings:   Mapped[List["Setting"]]  = relationship(back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[List["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    units:      Mapped[List["Unit"]]     = relationship(back_populates="user", cascade="all, delete-orphan")
    tags:       Mapped[List["Tag"]]      = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Setting(Base):
    """Per-user key/value settings store (currency, theme, default_vault, etc.)"""
    __tablename__ = "settings"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_settings_user_key"),
    )

    setting_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:    Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    key:        Mapped[str] = mapped_column(String(100), nullable=False)
    value:      Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship(back_populates="settings")

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value} for user_id={self.user_id}>"


class Vault(Base):
    __tablename__ = "vaults"
    __table_args__ = (
        UniqueConstraint("vault_name", "user_id", name="uq_vault_name_user"),
    )

    vault_id:   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    vault_name: Mapped[str]           = mapped_column(String(100), nullable=False)
    user_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    balance:    Mapped[float]         = mapped_column(Float, nullable=False, default=0.0)
    # NULL = inherit from user's currency setting. Set explicitly for multi-currency vaults.
    currency:   Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    user:         Mapped["User"]             = relationship(back_populates="vaults")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="vault", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vault {self.vault_name} balance={self.balance}>"


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Each user can have their own category with the same name.
        # user_id nullable=True allows the column to be added in migration without a default.
        UniqueConstraint("user_id", "category_name", name="uq_category_user_name"),
    )

    category_id:   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str]           = mapped_column(String(100), nullable=False)
    user_id:       Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True
    )

    user:         Mapped[Optional["User"]]    = relationship(back_populates="categories")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.category_name} user_id={self.user_id}>"


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("user_id", "unit_name", name="uq_unit_user_name"),
    )

    unit_id:   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_name: Mapped[str]           = mapped_column(String(50), nullable=False)
    user_id:   Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True
    )

    user:         Mapped[Optional["User"]]    = relationship(back_populates="units")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="unit")

    def __repr__(self) -> str:
        return f"<Unit {self.unit_name} user_id={self.user_id}>"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('Deposit', 'Withdraw', 'Transfer', 'Loan')",
            name="ck_transaction_type"
        ),
        Index("idx_transactions_vault_id", "vault_id"),
        Index("idx_transactions_date", "date"),
        Index("idx_transactions_type", "transaction_type"),
    )

    transaction_id:        Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    vault_id:              Mapped[int]           = mapped_column(Integer, ForeignKey("vaults.vault_id", ondelete="CASCADE"), nullable=False)
    transaction_type:      Mapped[str]           = mapped_column(String(20), nullable=False)
    amount:                Mapped[float]         = mapped_column(Float, nullable=False)
    category_id:           Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.category_id", ondelete="SET NULL"), nullable=True)
    description:           Mapped[str]           = mapped_column(Text, nullable=False, default="")
    comment:               Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity:              Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_id:               Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("units.unit_id", ondelete="SET NULL"), nullable=True)
    date:                  Mapped[str]           = mapped_column(String(30), nullable=False)
    linked_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transactions.transaction_id", ondelete="SET NULL"), nullable=True)
    # Phase 3.5 additions
    location:     Mapped[Optional[str]] = mapped_column(Text, nullable=True)       # "Carrefour", "Online", etc. Advanced/optional.
    is_recurring: Mapped[int]           = mapped_column(Integer, nullable=False, default=0)  # ML-use only, hidden from UI. 0=False, 1=True

    # Relationships
    vault:    Mapped["Vault"]              = relationship(back_populates="transactions")
    category: Mapped[Optional["Category"]] = relationship(back_populates="transactions")
    unit:     Mapped[Optional["Unit"]]     = relationship(back_populates="transactions")
    tags:     Mapped[List["Tag"]]          = relationship(secondary="transaction_tags", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type} {self.amount} on {self.date}>"


class Tag(Base):
    """Per-user labels that can be freely applied to any transaction (many-to-many)."""
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "tag_name", name="uq_tag_user_name"),
    )

    tag_id:   Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id:  Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    user:         Mapped["User"]              = relationship(back_populates="tags")
    transactions: Mapped[List["Transaction"]] = relationship(secondary="transaction_tags", back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag {self.tag_name} user_id={self.user_id}>"


class TransactionTag(Base):
    """Junction table — links transactions to tags (many-to-many)."""
    __tablename__ = "transaction_tags"

    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.transaction_id", ondelete="CASCADE"), primary_key=True)
    tag_id:         Mapped[int] = mapped_column(Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True)


class Loan(Base):
    """Placeholder for future loan tracking feature."""
    __tablename__ = "loans"

    from_vault_id: Mapped[int]   = mapped_column(Integer, ForeignKey("vaults.vault_id"), primary_key=True)
    to_vault_id:   Mapped[int]   = mapped_column(Integer, ForeignKey("vaults.vault_id"), primary_key=True)
    amount:        Mapped[float] = mapped_column(Float, nullable=False)