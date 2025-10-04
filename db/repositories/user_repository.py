
from ..db import Database
from typing import Any, Dict, Optional, List
import sqlite3


class UserRepository:

    def __init__(self, db: Database) -> None:
        """Initialize the UserRepository with a Database instance."""
        self.db: Database = db

    def add_user(self, username: str, email: str) -> int:

        """Add a new user to the database. Returns the new user's ID."""

        cur: sqlite3.Cursor = self.db.execute(
            query="INSERT INTO users (username, email) VALUES (?, ?)",
            params=(username, email),
            commit=True
        )
        return cur.lastrowid

    def get_user(self, uid: int) -> Optional[Dict[str, Any]]:

        """Retrieve a user by ID. Returns a dictionary or None if not found."""

        cur: sqlite3.Cursor = self.db.execute(
            query="SELECT id, username, email, trust_score, reports_made, created_at FROM users WHERE id = ?",
            params=(uid,),
            commit=False
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

    def get_user_id(self, username: str) -> Optional[int]:

        """Retrieve a user's ID by username. Returns the ID or None if not found."""

        cur: sqlite3.Cursor = self.db.execute(
            query="SELECT id FROM users WHERE username = ?",
            params=(username,),
            commit=False
        )
        row: Any = cur.fetchone()
        if row:
            return row[0]
        return None

    def update_trust_score(self, uid: int, score: float) -> None:

        """Update the trust score of a user."""

        self.db.execute(
            query="UPDATE users SET trust_score = ? WHERE id = ?",
            params=(score, uid),
            commit=True
        )

    def delete_user(self, uid: int) -> None:

        """Delete a user by ID."""

        self.db.execute(
            query="DELETE FROM users WHERE id = ?",
            params=(uid,),
            commit=True
        )

    def update_reports_made(self, uid: int, count: int) -> None:

        """Update the number of reports made by a user."""
        
        self.db.execute(
            query="UPDATE users SET reports_made = ? WHERE id = ?",
            params=(count, uid),
            commit=True
        )

    def list_users(self) -> List[Dict[str, Any]]:

        """List all users in the database."""

        cur: sqlite3.Cursor = self.db.execute(
            query="SELECT id, username, email, trust_score, reports_made, created_at FROM users",
            params=(),
            commit=False
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

