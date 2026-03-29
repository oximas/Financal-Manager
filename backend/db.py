"""
backend/db.py
-------------
Extended database layer for the FastAPI backend.
Inherits from the existing Database class and adds:
  - Transaction querying with filters & pagination
  - Settings CRUD
  - Per-user categories & units management
  - Password hashing support
  - Vault deletion / rename
  - Linked transfer awareness
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Make sure the project root is on the path so we can import core/data
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.database import Database as _BaseDatabase
import bcrypt as _bcrypt


class Database(_BaseDatabase):
    """
    Drop-in replacement for the original Database class, extended for the API.
    All original methods are preserved unchanged.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        # Enable foreign keys every connection (SQLite requires this each time)
        self.conn.execute("PRAGMA foreign_keys = ON")

    # ── Auth / Password ───────────────────────────────────────────────────────

    def check_user_password(self, username: str, password: str) -> bool:
        """
        Verify password — supports both bcrypt hashes and legacy plaintext
        (legacy is checked but immediately upgraded to bcrypt on success).
        """
        username = self._normalize_username(username)
        self.c.execute(
            "SELECT password FROM users WHERE username = ?", (username,)
        )
        row = self.c.fetchone()
        if row is None:
            return False

        stored = row[0]
        if stored is None:
            return False

        # Bcrypt hash
        if stored.startswith("$2b$") or stored.startswith("$2a$"):
            return _bcrypt.checkpw(password.encode("utf-8")[:72], stored.encode("utf-8"))

        # Legacy plaintext — verify then upgrade
        if stored == password:
            self._upgrade_password(username, password)
            return True

        return False

    def _upgrade_password(self, username: str, plaintext: str) -> None:
        """Transparently upgrade a plaintext password to bcrypt."""
        hashed = pwd_ctx.hash(plaintext)
        self.c.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed, username)
        )
        self.conn.commit()

    def add_user(self, username: str, password: Optional[str] = None) -> None:
        """Override: hash password before storing."""
        username = self._normalize_username(username)
        hashed = _bcrypt.hashpw(password.encode("utf-8")[:72], _bcrypt.gensalt()).decode("utf-8") if password else None

        self.c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        user_id = self.get_user_id(username)
        self.c.execute(
            "INSERT INTO vaults (user_id, vault_name, balance) VALUES (?, ?, 0)",
            (user_id, "Main")
        )
        # Seed default settings
        self.c.execute(
            "INSERT OR IGNORE INTO settings (user_id, currency) VALUES (?, 'EGP')",
            (user_id,)
        )
        self.conn.commit()

    # ── Settings ──────────────────────────────────────────────────────────────

    def get_settings(self, username: str) -> Dict[str, Any]:
        user_id = self.get_user_id(username)
        self.c.execute(
            "SELECT currency FROM settings WHERE user_id = ?", (user_id,)
        )
        row = self.c.fetchone()
        if row is None:
            # Settings row missing — create it (handles users created before migration)
            self.c.execute(
                "INSERT INTO settings (user_id, currency) VALUES (?, 'EGP')",
                (user_id,)
            )
            self.conn.commit()
            return {"currency": "EGP"}
        return {"currency": row[0]}

    def update_settings(self, username: str, currency: str) -> None:
        user_id = self.get_user_id(username)
        self.c.execute(
            "INSERT INTO settings (user_id, currency) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET currency = excluded.currency",
            (user_id, currency)
        )
        self.conn.commit()

    # ── Transactions — Query ──────────────────────────────────────────────────

    def get_transactions(
        self,
        username: str,
        vault_name: Optional[str] = None,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions for a user with optional filters.
        Returns list of dicts — ready to serialize to JSON.
        """
        user_id = self.get_user_id(username)

        query = """
            SELECT
                t.transaction_id,
                v.vault_name,
                t.transaction_type,
                t.amount,
                c.category_name,
                t.description,
                t.comment,
                t.quantity,
                u.unit_name,
                t.date,
                t.linked_transaction_id
            FROM transactions t
            LEFT JOIN vaults      v ON t.vault_id     = v.vault_id
            LEFT JOIN categories  c ON t.category_id  = c.category_id
            LEFT JOIN units       u ON t.unit_id       = u.unit_id
            WHERE v.user_id = ?
        """
        params: list = [user_id]

        if vault_name:
            query += " AND v.vault_name = ?"
            params.append(vault_name)

        if transaction_type:
            query += " AND LOWER(t.transaction_type) = LOWER(?)"
            params.append(transaction_type)

        if category:
            query += " AND c.category_name = ?"
            params.append(category)

        if search:
            query += " AND (LOWER(t.description) LIKE LOWER(?) OR LOWER(COALESCE(t.comment,'')) LIKE LOWER(?))"
            params.extend([f"%{search}%", f"%{search}%"])

        if date_from:
            query += " AND t.date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND t.date <= ?"
            params.append(date_to + " 23:59:59")

        query += " ORDER BY t.date DESC, t.transaction_id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        self.c.execute(query, params)
        rows = self.c.fetchall()

        cols = [
            "transaction_id", "vault_name", "transaction_type", "amount",
            "category_name", "description", "comment", "quantity",
            "unit_name", "date", "linked_transaction_id"
        ]
        return [dict(zip(cols, row)) for row in rows]

    def count_transactions(
        self,
        username: str,
        vault_name: Optional[str] = None,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> int:
        """Return total count matching the same filters (for pagination)."""
        user_id = self.get_user_id(username)

        query = """
            SELECT COUNT(*)
            FROM transactions t
            LEFT JOIN vaults     v ON t.vault_id    = v.vault_id
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE v.user_id = ?
        """
        params: list = [user_id]

        if vault_name:
            query += " AND v.vault_name = ?"
            params.append(vault_name)
        if transaction_type:
            query += " AND LOWER(t.transaction_type) = LOWER(?)"
            params.append(transaction_type)
        if category:
            query += " AND c.category_name = ?"
            params.append(category)
        if search:
            query += " AND (LOWER(t.description) LIKE LOWER(?) OR LOWER(COALESCE(t.comment,'')) LIKE LOWER(?))"
            params.extend([f"%{search}%", f"%{search}%"])
        if date_from:
            query += " AND t.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND t.date <= ?"
            params.append(date_to + " 23:59:59")

        self.c.execute(query, params)
        return self.c.fetchone()[0]

    def get_transaction_by_id(self, transaction_id: int, username: str) -> Optional[Dict[str, Any]]:
        """Fetch a single transaction, enforcing ownership."""
        user_id = self.get_user_id(username)
        self.c.execute("""
            SELECT
                t.transaction_id, v.vault_name, t.transaction_type, t.amount,
                c.category_name, t.description, t.comment, t.quantity,
                u.unit_name, t.date, t.linked_transaction_id
            FROM transactions t
            LEFT JOIN vaults     v ON t.vault_id    = v.vault_id
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN units      u ON t.unit_id      = u.unit_id
            WHERE t.transaction_id = ? AND v.user_id = ?
        """, (transaction_id, user_id))
        row = self.c.fetchone()
        if row is None:
            return None
        cols = [
            "transaction_id", "vault_name", "transaction_type", "amount",
            "category_name", "description", "comment", "quantity",
            "unit_name", "date", "linked_transaction_id"
        ]
        return dict(zip(cols, row))

    def update_transaction_comment(
        self, transaction_id: int, comment: str, username: str
    ) -> bool:
        """Update the comment on a transaction. Returns True if updated."""
        user_id = self.get_user_id(username)
        self.c.execute("""
            UPDATE transactions
            SET comment = ?
            WHERE transaction_id = ?
              AND vault_id IN (SELECT vault_id FROM vaults WHERE user_id = ?)
        """, (comment, transaction_id, user_id))
        self.conn.commit()
        return self.c.rowcount > 0

    # ── Transaction deposit/withdraw — extended with comment ──────────────────

    def add_transaction(
        self,
        username: str,
        vault_name: str,
        transaction_type: str,
        money_amount: float,
        category: str,
        description: str,
        quantity=None,
        unit=None,
        date=None,
        comment: Optional[str] = None,
        linked_transaction_id: Optional[int] = None,
    ) -> int:
        """Extended version that also stores comment and linked_transaction_id. Returns new ID."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        vault_id = self.get_vault_id(username, vault_name)
        category_id = self.get_category_id(category)
        unit_id = self.get_unit_id(unit) if unit else None

        self.c.execute(
            """INSERT INTO transactions
               (vault_id, transaction_type, amount, category_id, description,
                quantity, unit_id, date, comment, linked_transaction_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                vault_id, transaction_type, money_amount, category_id,
                description.lower(), quantity, unit_id, date,
                comment, linked_transaction_id
            )
        )
        self.conn.commit()
        return self.c.lastrowid

    def transfer(
        self,
        from_user, from_vault, to_user, to_vault, amount,
        description=None, date=None, comment=None
    ) -> None:
        """Override transfer to link the two transaction records."""
        description = description or "transferring money"

        self.remove_from_vault(from_user, from_vault, amount)
        self.add_to_vault(to_user, to_vault, amount)

        t1_id = self.add_transaction(
            from_user, from_vault, "transfer",
            amount, "Others", description,
            date=date, comment=comment
        )
        t2_id = self.add_transaction(
            to_user, to_vault, "transfer",
            amount, "Others", description,
            date=date, comment=comment
        )

        # Link the two sides
        self.c.execute(
            "UPDATE transactions SET linked_transaction_id = ? WHERE transaction_id = ?",
            (t2_id, t1_id)
        )
        self.c.execute(
            "UPDATE transactions SET linked_transaction_id = ? WHERE transaction_id = ?",
            (t1_id, t2_id)
        )
        self.conn.commit()

    # ── Categories ────────────────────────────────────────────────────────────

    def get_category_names(self, username: Optional[str] = None) -> List[str]:
        """Return global categories + user's personal ones."""
        if username:
            try:
                user_id = self.get_user_id(username)
                self.c.execute(
                    "SELECT category_name FROM categories "
                    "WHERE user_id IS NULL OR user_id = ? "
                    "ORDER BY user_id NULLS FIRST, category_name",
                    (user_id,)
                )
            except ValueError:
                self.c.execute(
                    "SELECT category_name FROM categories WHERE user_id IS NULL"
                )
        else:
            self.c.execute("SELECT category_name FROM categories WHERE user_id IS NULL")
        return [r[0] for r in self.c.fetchall()]

    def add_category(self, category_name: str, username: Optional[str] = None) -> None:
        """Add a category. If username given it's personal, otherwise global."""
        user_id = self.get_user_id(username) if username else None
        self.c.execute(
            "INSERT OR IGNORE INTO categories (category_name, user_id) VALUES (?, ?)",
            (category_name, user_id)
        )
        self.conn.commit()

    def delete_category(self, category_name: str, username: str) -> bool:
        """Delete a personal category (cannot delete global ones)."""
        user_id = self.get_user_id(username)
        self.c.execute(
            "DELETE FROM categories WHERE category_name = ? AND user_id = ?",
            (category_name, user_id)
        )
        self.conn.commit()
        return self.c.rowcount > 0

    # ── Units ─────────────────────────────────────────────────────────────────

    def get_unit_names(self, username: Optional[str] = None) -> List[str]:
        """Return global units + user's personal ones."""
        if username:
            try:
                user_id = self.get_user_id(username)
                self.c.execute(
                    "SELECT unit_name FROM units "
                    "WHERE user_id IS NULL OR user_id = ? "
                    "ORDER BY unit_id",
                    (user_id,)
                )
            except ValueError:
                self.c.execute("SELECT unit_name FROM units WHERE user_id IS NULL")
        else:
            self.c.execute("SELECT unit_name FROM units WHERE user_id IS NULL")
        return [r[0] for r in self.c.fetchall()]

    def add_unit(self, unit_name: str, username: Optional[str] = None) -> None:
        user_id = self.get_user_id(username) if username else None
        self.c.execute(
            "INSERT OR IGNORE INTO units (unit_name, user_id) VALUES (?, ?)",
            (unit_name, user_id)
        )
        self.conn.commit()

    # ── Vaults — extended ─────────────────────────────────────────────────────

    def delete_vault(self, username: str, vault_name: str) -> bool:
        """
        Delete a vault. Only allowed if balance is 0.
        Returns True if deleted, False if balance non-zero.
        """
        user_id = self.get_user_id(username)
        self.c.execute(
            "SELECT balance FROM vaults WHERE user_id = ? AND vault_name = ?",
            (user_id, vault_name)
        )
        row = self.c.fetchone()
        if row is None:
            raise ValueError(f"Vault '{vault_name}' not found")
        if row[0] != 0:
            return False  # Caller should inform user to empty the vault first
        self.c.execute(
            "DELETE FROM vaults WHERE user_id = ? AND vault_name = ?",
            (user_id, vault_name)
        )
        self.conn.commit()
        return True

    def rename_vault(self, username: str, old_name: str, new_name: str) -> None:
        user_id = self.get_user_id(username)
        self.c.execute(
            "UPDATE vaults SET vault_name = ? WHERE user_id = ? AND vault_name = ?",
            (new_name.capitalize(), user_id, old_name)
        )
        self.conn.commit()

    # ── Summary / Dashboard ───────────────────────────────────────────────────

    def get_monthly_summary(self, username: str, year: int, month: int) -> Dict:
        """Income, expenses, net for a given month."""
        user_id = self.get_user_id(username)
        prefix = f"{year}-{month:02d}-%"

        self.c.execute("""
            SELECT
                SUM(CASE WHEN t.amount > 0 AND LOWER(t.transaction_type) = 'deposit' THEN t.amount ELSE 0 END) AS income,
                SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END)                                       AS expenses
            FROM transactions t
            JOIN vaults v ON t.vault_id = v.vault_id
            WHERE v.user_id = ? AND t.date LIKE ?
        """, (user_id, prefix))
        row = self.c.fetchone()
        income = row[0] or 0.0
        expenses = row[1] or 0.0
        return {
            "year": year,
            "month": month,
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "net": round(income - expenses, 2),
        }

    def get_spending_by_category(
        self, username: str, date_from: Optional[str] = None, date_to: Optional[str] = None
    ) -> List[Dict]:
        """Aggregate spending (withdrawals) per category."""
        user_id = self.get_user_id(username)
        params: list = [user_id]

        date_filter = ""
        if date_from:
            date_filter += " AND t.date >= ?"
            params.append(date_from)
        if date_to:
            date_filter += " AND t.date <= ?"
            params.append(date_to + " 23:59:59")

        self.c.execute(f"""
            SELECT c.category_name, SUM(ABS(t.amount)) AS total
            FROM transactions t
            JOIN vaults v ON t.vault_id = v.vault_id
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE v.user_id = ?
              AND LOWER(t.transaction_type) = 'withdraw'
              {date_filter}
            GROUP BY c.category_name
            ORDER BY total DESC
        """, params)
        return [{"category": r[0] or "Uncategorized", "total": round(r[1], 2)}
                for r in self.c.fetchall()]
