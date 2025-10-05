import sys
import os
import random
import datetime
from faker import Faker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import Database, ReportType, Status
from db.repositories.user_repository import UserRepository
from db.repositories.report_repository import ReportRepository
from db.repositories.incident_repository import IncidentRepository
from db.repositories.general_repository import GeneralRepository

fake = Faker()
Faker.seed(42)
db = Database("test.db")
user_repo = UserRepository(db)
report_repo = ReportRepository(db)
incident_repo = IncidentRepository(db)
general_repo = GeneralRepository(db)

# --- 1. Add report types if not present ---
db.fill_types()
report_types = list(ReportType.list())
type_ids = []
for rt in report_types:
    tid = general_repo.get_type_id(ReportType(rt))
    if tid is not None:
        type_ids.append(tid)

# --- 2. Add locations ---
location_names = [fake.street_name() for _ in range(10)]
location_ids = []
for name in location_names:
    loc_id = general_repo.get_location_id(name)
    if loc_id is None:
        loc_id = general_repo.add_location(name, (float(fake.latitude()), float(fake.longitude())))
    location_ids.append(loc_id)
print(location_ids)
# --- 3. Add users ---
user_ids = []
for _ in range(20):
    username = fake.user_name()
    email = fake.email()
    uid = user_repo.get_user_id(username)
    if uid is None:
        uid = user_repo.add_user(username, email)
    user_ids.append(uid)

# --- 4. Add reports ---
report_ids = []
for _ in range(200):
    user_id = random.choice(user_ids)
    location_id = random.choice(location_ids)
    type_id = random.choice(type_ids)
    delay_minutes = random.randint(0, 60)
    report_id = report_repo.add_report(user_id, location_id, type_id, delay_minutes)
    report_ids.append(report_id)

# --- 5. Add incidents ---
num_incidents = 3000
num_zero_delay = int(num_incidents * 0.5)
num_nonzero_delay = num_incidents - num_zero_delay

# First, add 30% with 0 min delay
for _ in range(num_zero_delay):
    location_id = random.choice(location_ids)
    type_id = random.choice(type_ids)
    avg_delay = 0.0
    trust_score = random.uniform(0.0, 1.0)
    status = random.choice(list(Status.list()))
    created_at = fake.date_time_between(start_date='-30d', end_date='now')
    db.execute(
        "INSERT INTO incidents (location_id, type_id, avg_delay, trust_score, status, created_at, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (location_id, type_id, avg_delay, trust_score, status, created_at, created_at),
        commit=True
    )

for _ in range(num_nonzero_delay):
    location_id = random.choice(location_ids)

    type_id = random.choice(type_ids)

    location_multiplier = {
        1: 0.2,
        2: 0.4,
        3: 0.6,
        4: 0.8,
        5: 1.0,
        6: 1.2,
        7: 1.4,
        8: 1.6,
        9: 1.8,
        10: 2.0
    }
    avg_delay = random.gauss(10, 5) * location_multiplier[location_id]

    trust_score = random.uniform(0.0, 1.0)
    status = random.choice(list(Status.list()))

    # Random date in the last 30 days
    created_at = fake.date_time_between(start_date='-30d', end_date='now')
    db.execute(
        "INSERT INTO incidents (location_id, type_id, avg_delay, trust_score, status, created_at, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (location_id, type_id, avg_delay, trust_score, status, created_at, created_at),
        commit=True
    )

print("Fake data generation complete.")
db.close()