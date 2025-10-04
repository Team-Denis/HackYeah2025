
import sqlite3
from typing import List, Tuple
from dataclasses import dataclass, field


@dataclass
class Table:

    USER: str = field(default="""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            trust_score REAL DEFAULT 1.0,
            reports_made INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    REPORT_TYPE: str = field(default="""
        CREATE TABLE IF NOT EXISTS report_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """)

    LOCATION: str = field(default="""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            line_id TEXT,
            coords_lat REAL,
            coords_lon REAL
        );
    """)

    INCIDENT: str = field(default="""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            avg_delay REAL,
            trust_score REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active', -- active / resolved / pending
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
            FOREIGN KEY (type_id) REFERENCES report_types(id)
        );
    """)

    REPORT: str = field(default="""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            incident_id INTEGER,
            location_id INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            delay_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE SET NULL,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
            FOREIGN KEY (type_id) REFERENCES report_types(id)
        );
    """)

    def list(self) -> List[str]:
        return [value for key, value in self.__dict__.items() \
                if not key.startswith('_')]
    

class Database:

    def __init__(self, fp: str) -> None:

        """Initialize the database connection and enable foreign key support."""

        self.conn: sqlite3.Connection = sqlite3.connect(fp)
        self.cursor: sqlite3.Cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")


    def init_tables(self) -> None:

        """Initialize all tables in the database."""

        for t in Table().list():
            self.cursor.execute(t)
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:

        """
        Execute a query with optional parameters. Returns the cursor. \n
        Raises SQLite exceptions on error.
        """

        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur