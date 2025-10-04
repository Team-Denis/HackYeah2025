
from db import Database
from typing import Any




class Aggregator:
    
    def __init__(self, db: Database) -> None:
        self.db: Database = db

    def aggregate(self) -> Any:
        ...