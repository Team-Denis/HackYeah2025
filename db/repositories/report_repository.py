
from ..db import Database
from typing import Any, Dict, List, Optional, Tuple
import sqlite3


class ReportRepository:

    def __init__(self, db: Database) -> None:
        """Initialize the ReportRepository with a Database instance."""
        self.db: Database = db

    def add_report(
        self,
        user_id: int,
        location_id: int,
        type_id: int,
        delay_minutes: Optional[int] = None
    ) -> int:
        
        """
        Insert a new report (raw signalement from user).
        Returns the new report ID.
        """

        cur: sqlite3.Cursor = self.db.execute(
            query="""
                INSERT INTO reports (user_id, location_id, type_id, delay_minutes)
                VALUES (?, ?, ?, ?)
            """,
            params=(user_id, location_id, type_id, delay_minutes),
        )

        user: Optional[Tuple[int]] = self.db.execute(
            query="SELECT reports_made FROM users WHERE id = ?",
            params=(user_id,),
        ).fetchone()

        if user:
            new_count = (user[0] or 0) + 1
            self.db.execute(
                query="UPDATE users SET reports_made = ? WHERE id = ?",
                params=(new_count, user_id),
            )

        return cur.lastrowid

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:

        """Retrieve a report by ID."""

        cur: sqlite3.Cursor = self.db.execute(
            query="""
                SELECT id, user_id, location_id, type_id, delay_minutes, created_at
                FROM reports WHERE id = ?
            """,
            params=(report_id,),
        )

        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "location_id": row[2],
                "type_id": row[3],
                "delay_minutes": row[4],
                "created_at": row[5]
            }
        
        return None

    def list_reports(
        self,
        location_id: Optional[int] = None,
        type_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        
        """
        List reports, optionally filtered by location or type.
        Returns reports ordered by created_at descending.
        """

        query: str = """
            SELECT id, user_id, location_id, type_id, delay_minutes, created_at
            FROM reports
        """
        params: Tuple = ()
        filters: List[str] = []

        if location_id is not None:
            filters.append("location_id = ?")
            params += (location_id,)
        if type_id is not None:
            filters.append("type_id = ?")
            params += (type_id,)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY created_at DESC"

        cur: sqlite3.Cursor = self.db.execute(query, params)
        rows: Any = cur.fetchall()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "location_id": r[2],
                "type_id": r[3],
                "delay_minutes": r[4],
                "created_at": r[5]
            }
            for r in rows
        ]

    def list_recent_reports(self, limit: int = 50) -> List[Dict[str, Any]]:

        """Get the most recent reports."""

        cur: sqlite3.Cursor = self.db.execute(
            query="""
                SELECT id, user_id, location_id, type_id, delay_minutes, created_at
                FROM reports
                ORDER BY created_at DESC
                LIMIT ?
            """,
            params=(limit,),
        )

        rows: Any = cur.fetchall()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "location_id": r[2],
                "type_id": r[3],
                "delay_minutes": r[4],
                "created_at": r[5]
            }
            for r in rows
        ]

    def assign_to_incident(self, report_id: int, incident_id: int) -> None:

        """Link a report to a given incident."""

        self.db.execute(
            query="UPDATE reports SET incident_id = ? WHERE id = ?",
            params=(incident_id, report_id),
        )

    def get_reports_by_incident(self, incident_id: int) -> List[Dict[str, Any]]:
        
        cur = self.db.execute(
            query="""
                SELECT id, user_id, location_id, type_id, delay_minutes, created_at
                FROM reports
                WHERE incident_id = ?
                ORDER BY created_at DESC
            """,
            params=(incident_id,),
        )
        rows = cur.fetchall()
        
        return [
            {
                "id": r[0],
                "user_id": r[1],
                "location_id": r[2],
                "type_id": r[3],
                "delay_minutes": r[4],
                "created_at": r[5]
            }
            for r in rows
        ]

