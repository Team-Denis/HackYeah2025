
from .aggregator import Aggregator
from .decider import Decider
from .report_message import ReportMessage
from db import Database
from typing import Tuple


class Routine:

    def __init__(self, db: Database) -> None:

        """Initialize the Routine with a Database instance."""

        self.db: Database = db
        self.aggregator: Aggregator = Aggregator(db)
        self.decider: Decider = Decider(db)

    def process_report(self, report: ReportMessage) -> None:

        """Process an incoming report message."""

        # Step 1: Decide if the report is valid
        k: Tuple[bool, float] = self.decider.decide(report)
        if not k[0]:
            print(f"[INFO] Report from {report.user_name} rejected (with {k[1]}).")
            return
        
        print(f"[INFO] Report from {report.user_name} accepted (with {k[1]}).")
        
        # Step 2: Aggregate the report into the system
        self.aggregator.routine(report)
        print(f"[INFO] Report from {report.user_name} processed.")

        # Step 3: Send notifications to GTFS system
        # TODO: Implement GTFS notification logic here

       