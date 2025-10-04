
from ..db import Database
from typing import Any, Dict, List, Optional, Tuple
import sqlite3


class IncidentRepository:

    def __init__(self, db: Database) -> None:
        """Initialize the IncidentRepository with a Database instance."""
        self.db: Database = db

    def add_incident(
        self,
        location_id: int,
        type_id: int,
        avg_delay: Optional[float] = None,
        trust_score: float = 0.0,
        status: str = 'active'
    ) -> int:
        
        """
        Insert a new incident.
        Returns the new incident ID.
        """

        cur: sqlite3.Cursor = self.db.execute(
            query="""
                INSERT INTO incidents (location_id, type_id, avg_delay, trust_score, status)
                VALUES (?, ?, ?, ?, ?)
            """,
            params=(location_id, type_id, avg_delay, trust_score, status),
            commit=True
        )
        return cur.lastrowid

    def get_incident(self, incident_id: int) -> Optional[Dict[str, Any]]:

        """Retrieve an incident by ID."""

        cur: sqlite3.Cursor = self.db.execute(
            query="""
                SELECT id, location_id, type_id, avg_delay, trust_score, status, created_at, last_updated
                FROM incidents WHERE id = ?
            """,
            params=(incident_id,),
            commit=False
        )

        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "location_id": row[1],
                "type_id": row[2],
                "avg_delay": row[3],
                "trust_score": row[4],
                "status": row[5],
                "created_at": row[6],
                "last_updated": row[7]
            }
        return None

    def update_incident(
        self,
        incident_id: int,
        avg_delay: Optional[float] = None,
        trust_score: Optional[float] = None,
        status: Optional[str] = None
    ) -> None:
        
        """Update fields of an incident."""

        updates: List[str] = []
        params: List[Any] = []

        if avg_delay is not None:
            updates.append("avg_delay = ?")
            params.append(avg_delay)
        if trust_score is not None:
            updates.append("trust_score = ?")
            params.append(trust_score)
        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if updates:
            params.append(incident_id)
            query = f"UPDATE incidents SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP WHERE id = ?"
            self.db.execute(query=query, params=tuple(params), commit=True)

    def delete_incident(self, incident_id: int) -> None:
        """Delete an incident by ID."""
        self.db.execute(
            query="DELETE FROM incidents WHERE id = ?",
            params=(incident_id,),
            commit=True
        )

    def list_incidents(
        self,
        location_id: Optional[int] = None,
        type_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        
        """List incidents optionally filtered by location, type or status."""

        query: str = """
            SELECT id, location_id, type_id, avg_delay, trust_score, status, created_at, last_updated
            FROM incidents
        """
        filters: List[str] = []
        params: Tuple = ()

        if location_id is not None:
            filters.append("location_id = ?")
            params += (location_id,)
        if type_id is not None:
            filters.append("type_id = ?")
            params += (type_id,)
        if status is not None:
            filters.append("status = ?")
            params += (status,)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY last_updated DESC"

        cur = self.db.execute(query=query, params=params, commit=False)
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "location_id": r[1],
                "type_id": r[2],
                "avg_delay": r[3],
                "trust_score": r[4],
                "status": r[5],
                "created_at": r[6],
                "last_updated": r[7]
            }
            for r in rows
        ]

    def get_reports_for_incident(self, incident_id: int) -> List[Dict[str, Any]]:
        
        """Retrieve all reports linked to a given incident."""
        
        cur = self.db.execute(
            query="""
                SELECT id, user_id, location_id, type_id, delay_minutes, created_at
                FROM reports
                WHERE incident_id = ?
                ORDER BY created_at DESC
            """,
            params=(incident_id,),
            commit=False
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

    def get_incident_by_location(self, lid: int) -> Optional[Dict[str, Any]]:
        """Get the most recent active incident by location ID."""
        cur: sqlite3.Cursor = self.db.execute(
            query="""
                SELECT id, location_id, type_id, avg_delay, trust_score, status, created_at, last_updated
                FROM incidents
                WHERE location_id = ? AND status = 'active'
                ORDER BY last_updated DESC
                LIMIT 1
            """,
            params=(lid,),
            commit=False
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "location_id": row[1],
                "type_id": row[2],
                "avg_delay": row[3],
                "trust_score": row[4],
                "status": row[5],
                "created_at": row[6],
                "last_updated": row[7]
            }
        return None
