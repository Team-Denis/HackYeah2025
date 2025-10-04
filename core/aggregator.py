
from db import Database, Status, ReportRepository, GeneralRepository, UserRepository, IncidentRepository
from typing import Any, Dict, List, Optional
from core.report_message import ReportMessage
import datetime


# ✅ - Grep the location ID or add it if it doesn't exist yet to the db (with loc)
# ✅ - Grep the report type ID
# ✅ - Grep user ID
# ✅ - Push the report to the database with correct loc and reptype
# ✅ - Update the user's report history (count)
# ✅ - Decide if the report should be aggregated.

# No (no active incident found with this loc)
# ✅ - Add a new incident with this report as the first report
# ✅ - Copy the report data to the incident data
# ✅ - Decide it's trust value
# ✅ - Set the incident as active

# Yes (active incident found with this loc)
# ✅ - Add the report to the incident's report list
# ✅ - Update the incident data USING a module with a strategy
# ✅ - Update the incident's last updated timestamp
# ✅ - If the incident was inactive, set it as active again
# ✅ - If the incident is resolved (report type resolved), close it.

class Aggregator:

    """
    Aggregates user reports into incidents and manages database interactions.
    """
    
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

    def _no_incident_subroutine(self, mids: Dict[str, int], r: ReportMessage) -> None:

        """Push the incident in the DB."""

        iid: int = self.incident_repo.add_incident(
            location_id=mids["lid"],
            type_id=mids["tid"],
            avg_delay=r.delay_minutes,
            trust_score=0.0,  # will be updated right after
            status='active'
        )

        # add the report to the incident's report list
        self.report_repo.assign_to_incident(mids["rid"], iid)

        # update the incident's trust score
        incident: Optional[Dict[str, Any]] = self.incident_repo.get_incident(iid)
        self._update_trust_score(incident)

    def _incident_subroutine(self, mids: Dict[str, int], r: ReportMessage, incident: Dict[str, Any]) -> None:
        
        """Aggregate the report in the existing incident."""

        # add the report to the incident's report list and update the incident's data
        self.report_repo.assign_to_incident(mids["rid"], incident["id"])
        self._update_trust_score(incident)

        # update the incident's data
        AggregatorHelper.update_incident(self, incident)

    def _update_trust_score(self, incident: Dict[str, Any]) -> None:

        """Update the trust score of an incident based on its reports."""

        trust_score: float = AggregatorHelper.calculate_trust_score(self, incident)
        self.incident_repo.update_trust_score(incident["id"], trust_score)



# We need to complete these methods (and potentially make others)
# to re calculate data for incidents, based on all reports related to it.
# This includes:
# - Trust score (more records = more trust, users with higher trust score)
# - Average delay (if applicable)
# - Incident type (most common report type / highest trust score report type
# or last report type if it's not resolved and there's no majority)
# - Status (if the last report is resolved, we can close the incident)
# - Last updated timestamp (just set it to now)
# !! Aggregator is done, doesnt need to be modified anymore !!


class AggregatorHelper:
    
    @staticmethod
    def calculate_trust_score(ag: Aggregator, incident: Dict[str, Any]) -> int:
        
        # get all reports for this incident
        reports: List[Dict[str, Any]] = ag.report_repo.get_reports_by_incident(
            incident["id"])
        assert len(reports) > 0, "[CRITICAL] No reports found for incident"
    
        # TODO: Implement trust score calculation logic

        score = 0.0

        # Calculate average delay time by reports to give smaller weight to outliers
        total_delay = 0
        for r in reports:
            if r["delay_minutes"] is not None:
                date = r["created_at"] + datetime.timedelta(minutes=r["delay_minutes"])
                total_delay += int(date.timestamp())

        avg_delay = total_delay / len(reports) if total_delay > 0 else 0

        weights = []
        for r in reports:

            weight = 1.0  # base weight

            user: Optional[Dict[str, Any]] = ag.user_repo.get_user_by_id(r["user_id"])
            if user is None:
                continue
            
            weight *= user["trust_score"]  # user trust score weight
            weight *= (1.0 + (user["reports_made"] / 100.0))  # user report count weight
            
            if r["delay_minutes"] is not None:
                # Delay time weight (reports close to avg_delay are more trustworthy)
                date = r["created_at"] + datetime.timedelta(minutes=r["delay_minutes"])
                delay_diff = abs(int(date.timestamp()) - avg_delay)
                if avg_delay > 0:
                    weight *= max(0.5, 1.0 - (delay_diff / avg_delay))  # reduce weight for outliers

            weights.append(weight)


        # Normalize score to be between 0.0 and 1.0
        max_weight = max(weights) if weights else 1.0
        for w in weights:
            score += w / max_weight
        if len(reports) > 0:
            score /= len(reports)

        return min(max(score, 0.0), 1.0)

    @staticmethod
    def update_incident(ag: Aggregator, incident: Dict[str, Any]) -> None:

        # update trust
        trust: float = AggregatorHelper.calculate_trust_score(ag, incident)
        ag.incident_repo.update_trust_score(incident["id"], trust)

        # TODO: update avg delay
        ...

        # TODO: update incident type
        ...

        # TODO: update status if needed
        ...

        # update last update field
        ag.incident_repo.update_last_updated(incident["id"])

