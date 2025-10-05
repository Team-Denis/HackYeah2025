
from .aggregator import Aggregator
from .decider import Decider
from .report_message import ReportMessage
from .user_elo import UserElo
from db import Database, UserRepository
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

        redis_conn: Redis = Redis(host='0.0.0.0', port=6379, db=0)
        print(f"[INFO] Listening for incoming reports.")

        while True:
            _, raw_message = redis_conn.blpop('report_queue')
            report: ReportMessage = ReportMessage.from_json(raw_message)
            self._process_report(report)

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

       