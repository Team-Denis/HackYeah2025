
from core import Routine
from db import Database, UserRepository, ReportType
from core import ReportMessage
import requests
import os
from dotenv import load_dotenv


def test_tb(db: Database) -> None:
    
    ur: UserRepository = UserRepository(db)
    uid1: int = ur.add_user('Ant0in', 'antoine.berthion@ulb.be')
    uid2: int = ur.add_user('bob', 'bob@bob.bob')

    rm1: ReportMessage = ReportMessage('Ant0in', (50, 20), '1_3',
        (50.06143, 19.93658), ReportType.DELAY, 10)
    rm2: ReportMessage = ReportMessage('bob', (50, 20), '1_3',
        (50.06143, 19.93658), ReportType.DELAY, 20)
    rm3: ReportMessage = ReportMessage('bob', (60, 20), '1_5',
        (60, 20), ReportType.ACCIDENT, None)
    
    url: str = f'http://{os.getenv("HOST")}:{os.getenv("PORT")}{os.getenv("ENQUEUE_ENDPOINT")}'
    assert url is not None, "ENQUEUE_URL env variable not set"

    requests.post(url, json=rm1.to_dict())
    requests.post(url, json=rm2.to_dict())
    requests.post(url, json=rm3.to_dict())


if __name__ == "__main__":

    load_dotenv()

    try: os.remove(os.getenv("DB_PATH"))
    except FileNotFoundError: ...

    db: Database = Database(os.getenv("DB_PATH"))
    db.fill_types()

    test_tb(db)
    
    routine: Routine = Routine(db)
    routine.run()

