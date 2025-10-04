
from ..db import Database, ReportType
from typing import Any, Dict, List, Optional, Tuple
import sqlite3


class GeneralRepository:

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_type_id(self, report_type: ReportType) -> Optional[int]:
        """Get the ID of a report type by its name. Returns None if not found."""

        cur = self.db.execute(
            query="SELECT id FROM report_types WHERE name = ?",
            params=(report_type.value,),
            commit=False
        )
        row: Optional[Tuple[int]] = cur.fetchone()
        return row[0] if row else None

