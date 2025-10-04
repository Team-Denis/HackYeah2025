

from db import (Database, UserRepository, ReportType,
                ReportRepository, IncidentRepository, GeneralRepository)
from core import (Decider, ReportMessage)
import os


if __name__ == "__main__":

    try: os.remove('app.db')
    except: pass

    db: Database = Database("app.db")
    db.fill_types()

    gr: GeneralRepository = GeneralRepository(db)
    # loc1id: int = gr.add_location("Rondo Barei", (50.0530281,19.9970389))
    # loc2id: int = gr.add_location("Kraków", (50.06143, 19.93658))
    # t1: int = gr.get_type_id(ReportType.DELAY)
    # t2: int = gr.get_type_id(ReportType.MAINTENANCE)

    ur: UserRepository = UserRepository(db)
    uid1: int = ur.add_user('Ant0in', 'antoine.berthion@ulb.be')
    uid2: int = ur.add_user('bob', 'bob@bob.bob')

    rr: ReportRepository = ReportRepository(db)
    rm1: ReportMessage = ReportMessage('Ant0in', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 10)
    
    decider: Decider = Decider(db)
    print(decider.decide(rm1))
    
    





