
from db import Database, UserRepository
from core.report_message import ReportMessage
from typing import Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class Thresholds:
    
    DISTANCE: float = 10.0  # km threshold
    TIME: float = 360  # 6 hours in minutes threshold
    TRUST: float = 0.7  # trust score threshold
    DECIDE: float = 0.5  # decision threshold


class Decider:

    PRIOR: float = 0.9
    PRIOR_WEIGHT: float = 1.0
    LOW_THRESHOLD: float = 0.5   

    def __init__(self, db: Database) -> None:

        """Initializes the Decider with a database instance."""

        self.db: Database = db
        self.user_repo: UserRepository = UserRepository(db)

    def decide(self, message: ReportMessage) -> bool:

        """
        Decides whether to trust a given report message.
        Combines distance, time, and user trust.
        """

        distance: float = self._distance(message)
        time_diff: Optional[float] = message.delay_minutes or 0.0
        trust_score: float = self._trust(message.user_id)

        if self._instant_reject(distance, time_diff, trust_score):
            return False

        score: float = (
            (trust_score * 2.0) - (distance / Thresholds.DISTANCE) - (time_diff / Thresholds.TIME)
        )
        prob: float = self._sigmoid(score)

        return prob >= Thresholds.DECIDE 

    def _distance(self, message: ReportMessage) -> float:

        """
        Calculates the Haversine distance between the user's
        location and the reported location.
        """

        lat1: float = message.user_location[0]
        lon1: float = message.user_location[1]
        lat2: float = message.reported_location[0]
        lon2: float = message.reported_location[1]

        # map to radians yuh
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat: float = lat2 - lat1
        dlon: float = lon2 - lon1
        R: float = 6371  # radius of earth in km

        a: float = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) \
            * math.sin(dlon/2)**2
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c  # km distance

    def _trust(self, user_id: str) -> bool:

        """
        Checks if the user is considered reliable based on past reports.
        """
        
        user: Dict[str, Any] = self.user_repo.get_user(user_id)
        trust_score: float = user['trust_score']
        reports_count: int = user['reports_count']

        prior: float = self.PRIOR
        prior_weight: float = self.PRIOR_WEIGHT
        low_threshold: float = self.LOW_THRESHOLD

        raw: float = (prior_weight * prior + reports_count * trust_score) / \
            (prior_weight + reports_count)

        return trust_score if trust_score <= low_threshold else raw

    @staticmethod
    def _instant_reject(distance: float, time_diff: float, trust_score: float) -> bool:

        """
        Determines if the report should be instantly rejected based on
        if the thresholds are exceeded.
        """

        if distance > Thresholds.DISTANCE:
            return True
        if time_diff > Thresholds.TIME:
            return True
        if trust_score < Thresholds.TRUST:
            return True

        # good
        return False

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Applies the sigmoid function to a given value."""
        return 1 / (1 + math.exp(-x))
    
        
        
