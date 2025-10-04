
from ..db import Database
from typing import Any, Dict, Optional, List
import sqlite3


class IncidentRepository:

    def __init__(self, db: Database) -> None:
        """Initialize the IncidentRepository with a Database instance."""
        self.db: Database = db