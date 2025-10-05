

from db import (Database, UserRepository, ReportType,
                ReportRepository, IncidentRepository, GeneralRepository)
from core import (ReportMessage, Routine)
import os
import requests
import threading


if __name__ == "__main__":

    try: os.remove('app.db')
    except: pass


    # rr: ReportRepository = ReportRepository(db)

    rm1: ReportMessage = ReportMessage('Ant0in', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 10)
    rm2: ReportMessage = ReportMessage('bob', (50, 20), 'Krakow',
        (50.06143, 19.93658), ReportType.DELAY, 20)
    rm3: ReportMessage = ReportMessage('bob', (60, 20), 'Varsovia',
        (60, 20), ReportType.ACCIDENT, None)
    
    
    # routine.process_report(rm1)
    # routine.process_report(rm2)
    # routine.process_report(rm3)

    # Try redis queue

    # convert messages to json
    url = os.getenv("ENQUEUE_URL", "http://localhost:5000/enqueue")


    requests.post(url, json=rm1.to_dict())
    requests.post(url, json=rm2.to_dict())
    requests.post(url, json=rm3.to_dict())

    print("Exiting main thread.")

    

    





