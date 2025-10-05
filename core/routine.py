
from .aggregator import Aggregator
from .decider import Decider
from .report_message import ReportMessage
from .user_elo import UserElo
from db import Database, UserRepository, ReportType
from typing import Tuple
from redis import Redis
import json

class Routine:

    def __init__(self, db: Database) -> None:

        """Initialize the Routine with a Database instance."""

        self.db: Database = db
        self.aggregator: Aggregator = Aggregator(db)
        self.decider: Decider = Decider(db)
        self.elo: UserElo = UserElo(db)
        self.user_repo: UserRepository = UserRepository(db)

    def run(self) -> None:

        """Main processing loop for incoming reports."""

        redis_conn = Redis(host='localhost', port=6379, db=0)
        pubsub = redis_conn.pubsub()
        pubsub.subscribe("report_queue")

        print("[INFO] Listening for incoming reports...")

        for message in pubsub.listen():
            print(f"[DEBUG] Received message: {message}")
            if message['type'] != 'message':
                continue

            data = json.loads(message['data'].replace(b"'", b'"'))
            report_type = None
            match data.get('report_type'):
                case 'DELAY':
                    report_type = ReportType.DELAY
                case 'MAINTENANCE':
                    report_type = ReportType.MAINTENANCE
                case 'ACCIDENT':
                    report_type = ReportType.ACCIDENT
                case 'SOLVED':
                    report_type = ReportType.SOLVED
                case 'OTHER':
                    report_type = ReportType.OTHER
                case _:
                    print(f"[ERROR] Unknown report type: {data.get('report_type')}")

            report_message = ReportMessage(
                user_name=data.get('user_name'),
                user_location=(
                    data.get('user_location').get('latitude'),
                    data.get('user_location').get('longitude')
                ),
                location_name=data.get('location_name'),
                location_pos=(
                    data.get('location_pos').get('latitude'),
                    data.get('location_pos').get('longitude')
                ),
                report_type=ReportType(report_type),
                delay_minutes=data.get('delay_minutes')
            )

            print(report_message)
            self._process_report(report_message)



    def _process_report(self, report: ReportMessage) -> None:

        """Process an incoming report message."""

        # Step 1: Decide if the report is valid
        user_id: int = UserRepository(self.db).get_user_id(report.user_name)

        k: Tuple[bool, float] = self.decider.decide(report)
        if not k[0]:
            print(f"[INFO] Report from {report.user_name} rejected (with {k[1]}).")
            # Penalize user trust score for false report
            new_elo: float = self.elo.compute_new_elo(user_id, False)
            self.user_repo.update_trust_score(user_id, new_elo)
            return
        
        # Reward user trust score for valid report
        new_elo: float = self.elo.compute_new_elo(user_id, True)
        self.aggregator.user_repo.update_trust_score(user_id, new_elo)

        print(f"[INFO] Report from {report.user_name} accepted (with {k[1]}).")
        
        # Step 2: Aggregate the report into the system
        self.aggregator.routine(report)
        print(f"[INFO] Report from {report.user_name} processed.")

        # Step 3: Send notifications to GTFS system
        # TODO: Implement GTFS notification logic here

       