
from ..db import Database, Status
from typing import Any, Dict, List, Optional, Tuple
import sqlite3
import datetime


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
    
    def get_incident_since(self, since: str) -> List[Dict[str, Any]]:
        """Retrieve incidents updated since a given timestamp."""
        cur: sqlite3.Cursor = self.db.execute(
            query="""
                SELECT id, location_id, type_id, avg_delay, trust_score, status, created_at, last_updated
                FROM incidents WHERE last_updated >= ?
                ORDER BY last_updated DESC
            """,
            params=(since,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "location_id": row[1],
                "type_id": row[2],
                "avg_delay": row[3],
                "trust_score": row[4],
                "status": row[5],
                "created_at": row[6],
                "last_updated": row[7]
            }
            for row in rows
        ]

    def delete_incident(self, incident_id: int) -> None:
        """Delete an incident by ID."""
        self.db.execute(
            query="DELETE FROM incidents WHERE id = ?",
            params=(incident_id,),
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

        cur = self.db.execute(query=query, params=params,)
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

    def update_trust_score(self, incident_id: int, new_score: float) -> None:

        """Update the trust score of an incident."""

        if 0 > new_score or 1 < new_score:
            raise ValueError(f"[CRITICAL] Trust score must be between 0.0 and 1.0 (got {new_score})")

        self.db.execute(
            query="""
                UPDATE incidents
                SET trust_score = ?, last_updated = datetime('now', 'utc')
                WHERE id = ?
            """,
            params=(new_score, incident_id),
        )

    def update_avg_delay(self, incident_id: int, new_delay: float) -> None:

        """Update the average delay of an incident."""

        if new_delay is not None:
            if new_delay < 0:
                raise ValueError("[CRITICAL] Average delay cannot be negative")

        self.db.execute(
            query="""
                UPDATE incidents
                SET avg_delay = ?, last_updated = datetime('now', 'utc')
                WHERE id = ?
            """,
            params=(new_delay, incident_id),
        )

    def update_last_updated(self, incident_id: int) -> None:

        """Update the last_updated timestamp of an incident to the current time."""

        self.db.execute(
            query="""
                UPDATE incidents
                SET last_updated = datetime('now', 'utc')
                WHERE id = ?
            """,
            params=(incident_id,),
        )

    def update_status(self, incident_id: int, new_status: Status) -> None:

        """Update the status of an incident."""

        if new_status not in Status.list():
            raise ValueError(f"[CRITICAL] Invalid status: {new_status}")

        self.db.execute(
            query="""
                UPDATE incidents
                SET status = ?, last_updated = datetime('now', 'utc')
                WHERE id = ?
            """,
            params=(new_status.value, incident_id),
        )
    
    def update_status_for_old_incidents(self):
        """Set Status to 'RESOLVED' if last_updated is older than created_at + avg_delay + 5 minutes."""
        self.db.execute(
           query="""
               UPDATE incidents
               SET status = 'RESOLVED'
               WHERE last_updated < created_at + INTERVAL avg_delay + 5 MINUTE
           """,
       )

    def update_incident_type(self, incident_id: int, nit: int) -> None:

        """Update the type of an incident."""

        self.db.execute(
            query="""
                UPDATE incidents
                SET type_id = ?, last_updated = datetime('now', 'utc')
                WHERE id = ?
            """,
            params=(nit, incident_id),
        )

