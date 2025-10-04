
from db import Database, ReportRepository, GeneralRepository, UserRepository, IncidentRepository
from typing import Any, Dict, Optional
from core.report_message import ReportMessage


# ✅ - Grep the location ID or add it if it doesn't exist yet to the db (with loc)
# ✅ - Grep the report type ID
# ✅ - Grep user ID
# ✅ - Push the report to the database with correct loc and reptype
# ✅ - Update the user's report history (count)
# ✅ - Decide if the report should be aggregated.

# No (no active incident found with this loc)
# ✅ - Add a new incident with this report as the first report
# ✅ - Copy the report data to the incident data
# - Decide it's trust value
# ✅ - Set the incident as active

# Yes (active incident found with this loc)
# - Add the report to the incident's report list
# - Update the incident data USING a module with a strategy
# - Update the incident's last updated timestamp
# - If the incident was inactive, set it as active again
# - If the incident is resolved (report type resolved), close it.

class Aggregator:
    
    def __init__(self, db: Database) -> None:

        """Initialize the Aggregator with a Database instance."""

        self.db: Database = db

        # few repo to handle db queries easily
        self.report_repo: ReportRepository = ReportRepository(db)
        self.general_repo: GeneralRepository = GeneralRepository(db)
        self.user_repo: UserRepository = UserRepository(db)
        self.incident_repo: IncidentRepository = IncidentRepository(db)

    def routine(self, report: ReportMessage) -> None:
        
        # get the correct IDs or add them if they don't exist
        # and push the report to the database
        mids: Dict[str, Any] = self._handle_ids(report)
        rid: int = self.report_repo.add_report(
            user_id=mids["uid"],
            location_id=mids["lid"],
            type_id=mids["tid"],
            delay_minutes=report.delay_minutes)
        mids['rid'] = rid

        # update the user's report count and trust score
        user: Dict[str, Any] = self.user_repo.get_user_by_id(mids["uid"])
        self._update_report_history(user)
        self._update_trust_score(user)
        
        # try to fetch an active incident at this location
        # and run correct subroutine
        incident: Optional[Dict[str, Any]] = self.incident_repo.get_incident_by_location(mids["lid"])

        if incident: self._incident_subroutine(mids, report, incident)
        else: self._no_incident_subroutine(mids, report)

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

    def _update_report_history(self, user: Dict[str, Any]) -> None:
        """Increment the report count for a user by 1."""
        self.user_repo.update_reports_made(user["id"], (user["reports_made"] + 1))

    def _update_trust_score(self, user: Dict[str, Any]) -> None:
        """Update the trust score of a user based on their report history."""
        pass  # TODO: Implement trust score logic

    def _no_incident_subroutine(self, mids: Dict[str, int], r: ReportMessage) -> None:

        """Push the incident in the DB."""

        _: int = self.incident_repo.add_incident(
            location_id=mids["lid"],
            type_id=mids["tid"],
            avg_delay=r.delay_minutes,
            trust_score=r.trust_score,
            status='active'
        )

    def _incident_subroutine(self, mids: Dict[str, int], r: ReportMessage, incident: Dict[str, Any]) -> None:
        
        """Aggregate the report in the existing incident."""
        pass  # TODO: Implement incident aggregation subroutine
