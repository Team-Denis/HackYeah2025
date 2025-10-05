

from db import (Database, UserRepository, ReportType,
                ReportRepository, IncidentRepository, GeneralRepository)
from core import (ReportMessage, Routine)
import os


if __name__ == "__main__":

    try: os.remove('app.db')
    except: pass

    db: Database = Database("app.db")
    db.fill_types()

    gr: GeneralRepository = GeneralRepository(db)
    ur: UserRepository = UserRepository(db)
    uid1: int = ur.add_user('Ant0in', 'antoine.berthion@ulb.be')
    uid2: int = ur.add_user('bob', 'bob@bob.bob')

    rr: ReportRepository = ReportRepository(db)

    rm1: ReportMessage = ReportMessage('Ant0in', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 10)
    rm2: ReportMessage = ReportMessage('bob', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 20)
    rm3: ReportMessage = ReportMessage('bob', (60, 20), 'Varsovia',
        (60, 20), ReportType.ACCIDENT, None)
    
    routine: Routine = Routine(db)
    routine.process_report(rm1)
    routine.process_report(rm2)
    routine.process_report(rm3)
    

    

    





