
from core import Routine
from db import Database, UserRepository, ReportType
from core import ReportMessage
import requests
import os


if __name__ == "__main__":

    try:
        os.remove("app.db")
    except FileNotFoundError:
        pass

    db: Database = Database("app.db")
    db.fill_types()

    ur: UserRepository = UserRepository(db)
    uid1: int = ur.add_user('Ant0in', 'antoine.berthion@ulb.be')
    uid2: int = ur.add_user('bob', 'bob@bob.bob')

    rm1: ReportMessage = ReportMessage('Ant0in', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 10)
    rm2: ReportMessage = ReportMessage('bob', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 20)
    rm3: ReportMessage = ReportMessage('bob', (60, 20), 'Varsovia',
        (60, 20), ReportType.ACCIDENT, None)
    
    url = os.getenv("ENQUEUE_URL", "http://localhost:5000/enqueue")

    requests.post(url, json=rm1.to_dict())
    requests.post(url, json=rm2.to_dict())
    requests.post(url, json=rm3.to_dict())
    routine: Routine = Routine(db)
    routine.run()

