
from core import Routine
from db import Database, UserRepository, ReportType
from core import ReportMessage
import requests
import os
from dotenv import load_dotenv


def test_tb(db: Database) -> None:
    
    ur: UserRepository = UserRepository(db)
    _: int = ur.add_user('demo', 'demo@demo.demo')

if __name__ == "__main__":

    load_dotenv()

    try: os.remove(os.getenv("DB_PATH"))
    except FileNotFoundError: ...

    db: Database = Database(os.getenv("DB_PATH"))
    db.fill_types()

    test_tb(db)
    
    routine: Routine = Routine(db)
    routine.run()

