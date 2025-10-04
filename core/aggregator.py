
from db import Database, ReportRepository, GeneralRepository, UserRepository, IncidentRepository
from typing import Any, Dict, List, Optional, Tuple
from .report_message import ReportMessage
import datetime


# alias for reading

report_t = Dict[str, Any]
incident_t = Dict[str, Any]
user_t = Dict[str, Any]


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
        user: user_t = self.user_repo.get_user_by_id(mids["uid"])
        self._update_report_history(user)
        self._update_trust_score(user)
        
        # try to fetch an active incident at this location
        # and run correct subroutine
        incident: Optional[incident_t] = self.incident_repo.get_incident_by_location(mids["lid"])

        if incident: self._incident_subroutine(mids, report, incident)
        else: self._no_incident_subroutine(mids, report)

    def _handle_ids(self, r: ReportMessage) -> report_t:
        
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

    def _update_report_history(self, user: user_t) -> None:
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
        incident: Optional[incident_t] = self.incident_repo.get_incident(iid)
        self._update_trust_score(incident)

    def _incident_subroutine(self, mids: Dict[str, int], r: ReportMessage, incident: incident_t) -> None:
        
        """Aggregate the report in the existing incident."""

        # add the report to the incident's report list and update the incident's data
        self.report_repo.assign_to_incident(mids["rid"], incident["id"])
        self._update_trust_score(incident)

        # update the incident's data
        AggregatorHelper.update_incident(self, incident)

    def _update_trust_score(self, incident: incident_t) -> None:

        """Update the trust score of an incident based on its reports."""

        trust_score: float = AggregatorHelper.calculate_trust_score(self, incident)
        self.incident_repo.update_trust_score(incident["id"], trust_score)




class AggregatorHelper:
    
    @staticmethod
    def _calculate_normalized_delays(reports: List[report_t]) -> Dict[report_t, Optional[int]]:

        """Calculate normalized times relative to the report starting timestamp and now."""

        d: Dict[report_t, int] = dict()

        for r in reports:
            if not (r["delay_minutes"] is None):
                date: datetime.timedelta = r["created_at"] + \
                    datetime.timedelta(minutes=r["delay_minutes"])
                d[r] = int(date.timestamp())
            else: d[r] = None

        return d

    @staticmethod
    def _calculate_average_time(reports: List[report_t]) -> Optional[float]:

        # first we normalize data by doing the sum of created at + timedelta(now, delay)
        delay: float = 0.0
        times: List[int] = AggregatorHelper._calculate_normalized_delays(reports).values()

        # for each non null wait time
        for t in times:
            delay += t

        delay /= len(times) if len(times) > 0 else None
        return delay

    @staticmethod
    def _calculate_trust_score(ag: Aggregator, reports: List[report_t], avg: Optional[float] = None) -> float:
        
        # Calculate a score of trust 

        score: float = 0.0
        weights: List[float] = list()
        normalized_delays: Dict[report_t, int] = AggregatorHelper._calculate_normalized_delays(reports)

        for r in reports:

            weight: float = 1.0  # base weight is 1.0
            user: user_t = ag.user_repo.get_user_id(r["user_id"])
            weight *= user["trust_score"]
            weight *= (1.0 + (user["reports_made"] / 100.0))

            if normalized_delays[r] is not None and avg is not None:
                # Delay time weight (reports close to avg_delay are more trustworthy)
                delay_diff: int = abs(int(normalized_delays[r]) - avg)
                if avg > 0:
                    weight *= max(0.5, 1.0 - (delay_diff / avg))  # reduce weight for outliers

            weights.append(weight)

        # Normalize score to be between 0.0 and 1.0
        max_weight = max(weights) if weights else 1.0
        for w in weights:
            score += w / max_weight
        if len(reports) > 0:
            score /= len(reports)

        return min(max(score, 0.0), 1.0)

    @staticmethod
    def _update_incident(ag: Aggregator, incident: incident_t) -> None:
        
        # get all reports for this incident
        reports: List[Dict[str, Any]] = ag.report_repo.get_reports_by_incident(incident["id"])
        assert len(reports) > 0, "[CRITICAL] No reports found for incident"

        avg: Optional[float] = AggregatorHelper._calculate_average_time(reports)
        trust: float = AggregatorHelper._calculate_trust_score(ag, reports, avg)
        
        # TODO: status and maybe more idk i dont remember

        ag.incident_repo.update_avg_delay(incident['id'], avg)
        ag.incident_repo.update_trust_score(incident['id'], trust)
        ag.incident_repo.update_last_updated(incident['id'])

