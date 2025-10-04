
import sqlite3
from typing import List, Tuple
from dataclasses import dataclass, field, fields


@dataclass
class Table:

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
            coords_lat REAL,
            coords_lon REAL
        );
    """)

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

    REPORT: str = field(default="""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            delay_minutes INTEGER,
            incident_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
            FOREIGN KEY (type_id) REFERENCES report_types(id),
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE SET NULL
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

    @staticmethod
    def list() -> List[str]:
        return [getattr(Table, f.name) for f in fields(Table)]
    

@dataclass
class ReportType:

    DELAY: str = "Delay"
    ACCIDENT: str = "Accident"
    MAINTENANCE: str = "Maintenance"
    CLOSURE: str = "Closure"
    OTHER: str = "Other"

    @staticmethod
    def list() -> List[str]:
        return [getattr(ReportType, f.name) for f in fields(ReportType)]


class Database:

    _INDEXES: List[str] = [
        "CREATE INDEX IF NOT EXISTS idx_reports_location ON reports(location_id);",
        "CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type_id);",
        "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(location_id);",
        "CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(type_id);",
        "CREATE INDEX IF NOT EXISTS idx_incidents_last_updated ON incidents(last_updated);"
    ]

    def __init__(self, fp: str) -> None:

        """Initialize the database connection and enable foreign key support."""

        self.conn: sqlite3.Connection = sqlite3.connect(fp)
        self.cursor: sqlite3.Cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

        self._init_tables()
        self._create_indexes()

    def _init_tables(self) -> None:

        """Initialize all tables in the database."""

        for t in Table.list():
            self.execute(query=t, commit=False)
        self.conn.commit()

    def _create_indexes(self) -> None:

        """Create necessary indexes for performance optimization."""

        for idx in self._INDEXES:
            self.execute(idx, commit=False)
        self.conn.commit()

    def fill_types(self) -> None:

        """Fill the report_types table with defined types."""

        for t in ReportType.list():
            try:
                self.execute(
                    query="INSERT INTO report_types (name) VALUES (?)",
                    params=(t,),
                    commit=False
                )
            except sqlite3.IntegrityError as e:
                print(f'Type "{t}" already exists. Skipping... ({e}).')
        self.conn.commit()

    def fill_locations(self) -> None:
        
        print('[WARNING] Location seeding not implemented yet.')
        ... # TODO: Implement location seeding

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def execute(self, query: str, params: Tuple = (), commit: bool = True) -> sqlite3.Cursor:

        """
        Execute a query with optional parameters. Returns the cursor. \n
        ## Commit changes to the database manually if commit is set
        ## to False! \n
        Raises `sqlite3.Error` exceptions on error.
        """

        cur = self.conn.cursor()
        cur.execute(query, params)
        if commit:
            self.conn.commit()
        return cur

