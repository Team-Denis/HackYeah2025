
from ..db import Database, ReportType
from typing import Optional, Tuple
import sqlite3


class GeneralRepository:

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_type_id(self, report_type: ReportType) -> Optional[int]:
        """Get the ID of a report type by its name. Returns None if not found."""

        cur: sqlite3.Cursor = self.db.execute(
            query="SELECT id FROM report_types WHERE name = ?",
            params=(report_type.value,),
        )
        row: Optional[Tuple[int]] = cur.fetchone()
        return row[0] if row else None
    
    def get_location_id(self, location_name: str) -> Optional[int]:

        """Get the ID of a location by its name. Returns None if not found."""
        
        cur: sqlite3.Cursor = self.db.execute(
            query="SELECT id FROM locations WHERE name = ?",
            params=(location_name,),
        )
        row: Optional[Tuple[int]] = cur.fetchone()
        return row[0] if row else None

    def add_location(self, location_name: str, pos: Tuple[float, float]) -> int:

        """Add a new location to the database. Returns the new location ID."""
        
        cur: sqlite3.Cursor = self.db.execute(
            query="INSERT INTO locations (name, coords_lat, coords_lon) VALUES (?, ?, ?)",
            params=(location_name, pos[0], pos[1]),
        )
        return cur.lastrowid

