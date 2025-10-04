
from .db import Database
from typing import Any, Dict, Optional, List
import sqlite3


class UserRepository:

    def __init__(self, db: Database) -> None:

        """Initialize the UserRepository with a Database instance."""

        self.db: Database = db

    def add_user(self, username: str, email: str) -> int:

        """Add a new user to the database. Returns the new user's ID."""

        cur: sqlite3.Cursor = self.db.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (username, email)
        )
        return cur.lastrowid

    def get_user(self, uid: int) -> Optional[Dict[str, Any]]:

        """Retrieve a user by ID. Returns a dictionary or None if not found."""

        cur: sqlite3.Cursor = self.db.execute(
            "SELECT id, username, email, trust_score, created_at FROM users WHERE id = ?",
            (uid,)
        )
        row: Any = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "trust_score": row[3],
                "reports_made": row[4],
                "created_at": row[5],
            }
        return None

    def update_trust_score(self, uid: int, score: float) -> None:

        """Update the trust score of a user."""

        self.db.execute(
            "UPDATE users SET trust_score = ? WHERE id = ?",
            (score, uid)
        )
        self.db.conn.commit()

    def delete_user(self, uid: int) -> None:

        """Delete a user by ID."""

        self.db.execute(
            "DELETE FROM users WHERE id = ?",
            (uid,)
        )
        self.db.conn.commit()

    def increment_reports_made(self, uid: int) -> None:

        """Increment the reports_made count for a user."""

        self.db.execute(
            "UPDATE users SET reports_made = reports_made + 1 WHERE id = ?",
            (uid,)
        )
        self.db.conn.commit()

    def list_users(self) -> List[Dict[str, Any]]:

        """List all users in the database."""

        cur: sqlite3.Cursor = self.db.execute(
            "SELECT id, username, email, trust_score, reports_made, created_at FROM users"
        )
        rows: List[Any] = cur.fetchall()
        return [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "trust_score": row[3],
                "reports_made": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

