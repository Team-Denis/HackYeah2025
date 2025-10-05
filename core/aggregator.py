
from db import Database, ReportType, ReportRepository, GeneralRepository, UserRepository, IncidentRepository
from typing import Any, Dict, List, Optional, Tuple
from .report_message import ReportMessage
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


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

        print(f'[INFO] Added record: {self.report_repo.get_report(rid)}')

        # update the user's report count and trust score
        user: user_t = self.user_repo.get_user(mids["uid"])
        self._update_report_history(user)
        self._update_user_trust_score(user)
        
        # try to fetch an active incident at this location
        # and run correct subroutine
        incident: Optional[incident_t] = self.incident_repo.get_incident_by_location(mids["lid"])

        if incident: self._incident_subroutine(mids, report, incident)
        else: self._no_incident_subroutine(mids, report)

    def _handle_ids(self, r: ReportMessage) -> report_t:

        """Handle id fetching as well as creating Location records if new."""
        
        tid: Optional[int] = self.general_repo.get_type_id(r.report_type)
        uid: Optional[int] = self.user_repo.get_user_id(r.user_name)
        lid: Optional[int] = self.general_repo.get_location_id(r.location_name)

        # No lid is okay, we add it to the DB.
        # No uid or tid is NOT okay, those MUST exist (no custom report types or
        # users that don't exist).
        if lid is None:
            lid = self.general_repo.add_location(r.location_name, r.location_pos)
            print(f'[INFO] New location discovered, adding {lid}.')
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
        print(f'[INFO] Updated user report count: {self.user_repo.get_user(user["id"])}')

    def _no_incident_subroutine(self, mids: Dict[str, int], r: ReportMessage) -> None:

        """Push the incident in the DB."""

        iid: int = self.incident_repo.add_incident(
            location_id=mids["lid"],
            type_id=mids["tid"],
            avg_delay=r.delay_minutes,
            trust_score=0.0,  # will be updated right after
            status='active'
        )
        print(f'[INFO] Added incident since report is new info ({self.incident_repo.get_incident(iid)})')

        # add the report to the incident's report list
        self.report_repo.assign_to_incident(mids["rid"], iid)
        print(f'[INFO] Report {mids["rid"]} assigned to incident {iid}')

        # update the incident
        incident: Optional[incident_t] = self.incident_repo.get_incident(iid)
        AggregatorHelper._update_incident(self, incident)

    def _incident_subroutine(self, mids: Dict[str, int], r: ReportMessage, incident: incident_t) -> None:
        
        """Aggregate the report in the existing incident."""

        # add the report to the incident's report list and update the incident's data
        self.report_repo.assign_to_incident(mids["rid"], incident["id"])
        self._update_trust_score(incident)

        # update the incident's data
        AggregatorHelper._update_incident(self, incident)

    def _update_user_trust_score(self, user: user_t) -> None:

        """Update the trust score of a user based on their report history."""

        # TODO: do that ig
        print('[WARN] Skipping updating user score...')



class AggregatorHelper:
    
    @staticmethod
    def _calculate_normalized_delays(reports: List[dict]) -> Dict[int, Optional[float]]:
        """
        Calculate normalized delays for each report relative to the current time.
        
        Returns a dict mapping report_id -> remaining delay (in minutes)
        or None if delay is not provided.
        """

        d: Dict[int, Optional[float]] = {}

        tz = ZoneInfo("Europe/Warsaw")  # TODO: add a field TZ to avoid hardcoding (not urgent)
        now = datetime.now(tz)

        for r in reports:
            if r["delay_minutes"] is not None:
                
                created_at = datetime.fromisoformat(r["created_at"])
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=tz)
                planned = created_at - timedelta(minutes=r["delay_minutes"])

                print(planned)
                print(now)
                
                # difference between planned end and now
                diff = planned - now
                remaining_minutes = diff.total_seconds() / 60

                d[r["id"]] = round(remaining_minutes, 2)  # keep 2 decimals
            else:
                d[r["id"]] = None

        print(f"[INFO] Normalized time table: {d}")
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
    def _calculate_type(ag: Aggregator, reports: List[report_t]) -> int:

        """Determine the most common report type among the reports."""

        type_count: Dict[int, int] = dict()

        # sort reports by created_at (datetime) descending
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        for r in reports:
            if r["type_id"] in type_count:
                type_count[r["type_id"]] += 1
            else:
                type_count[r["type_id"]] = 1

        s: int = ag.general_repo.get_type_id(ReportType.SOLVED)
        
        # if any is Resolved, then return resolved
        if s in type_count: return s

        # if no resolved, then the most common type is the incident type
        # last update is given in case of tie (by sorting)
        m: int = max(type_count, key=type_count.get)
        return m

    @staticmethod
    def _update_incident(ag: Aggregator, incident: incident_t) -> None:
        
        # get all reports for this incident
        reports: List[Dict[str, Any]] = ag.report_repo.get_reports_by_incident(incident["id"])
        assert len(reports) > 0, "[CRITICAL] No reports found for incident"

        avg: Optional[float] = AggregatorHelper._calculate_average_time(reports)
        trust: float = AggregatorHelper._calculate_trust_score(ag, reports, avg)
        type_id: int = AggregatorHelper._calculate_type(ag, reports)

        # TODO: status and maybe more idk i dont remember

        ag.incident_repo.update_incident_type(incident['id'], type_id)
        ag.incident_repo.update_avg_delay(incident['id'], avg)
        ag.incident_repo.update_trust_score(incident['id'], trust)
        ag.incident_repo.update_last_updated(incident['id'])

