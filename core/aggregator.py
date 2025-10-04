
from db import Database, ReportRepository, GeneralRepository, UserRepository
from typing import Any, Dict, Optional
from core.report_factory import ReportMessage


# ✅ - Grep the location ID or add it if it doesn't exist yet to the db (with loc)
# ✅ - Grep the report type ID
# ✅ - Grep user ID
# - Push the report to the database with correct loc and reptype
# - Update the user's report history (count)
# Decide if the report should be aggregated.

# No (no active incident found with this loc)
# - Add a new incident with this report as the first report
# - Copy the report data to the incident data
# - Set the incident as active

# Yes (active incident found with this loc)
# - Add the report to the incident's report list
# - Update the incident data USING a module with a strategy
# - Update the incident's last updated timestamp
# - If the incident was inactive, set it as active again
# - If the incident is resolved (report type resolved), close it.

class Aggregator:
    
    def __init__(self, db: Database) -> None:
        self.db: Database = db
        self.report_repo: ReportRepository = ReportRepository(db)
        self.general_repo: GeneralRepository = GeneralRepository(db)
        self.user_repo: UserRepository = UserRepository(db)

    def routine(self, report: ReportMessage) -> None:
        
        # get the correct IDs or add them if they don't exist
        ids: Dict[str, Any] = self._handle_ids(report)

    def _handle_ids(self, r: ReportMessage) -> Dict[str, Any]:
        
        tid: Optional[int] = self.general_repo.get_type_id(r.report_type)
        uid: Optional[int] = self.user_repo.get_user_id(r.user_name)
        lid: Optional[int] = self.general_repo.get_location_id(r.location_name)

        # No lid is okay, we add it to the DB.
        # No uid or tid is NOT okay, those MUST exist (no custom report types or
        # users that don't exist).
        if lid is None: lid = self.general_repo.add_location(r.location_name, r.location_pos)
        if uid is None: raise ValueError("[CRITICAL] User does not exist")
        if tid is None: raise ValueError("[CRITICAL] Report type does not exist")

        return {
            "tid": tid,
            "uid": uid,
            "lid": lid
        }