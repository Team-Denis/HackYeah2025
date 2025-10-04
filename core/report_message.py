
from dataclasses import dataclass
from typing import Tuple, Optional
from db import ReportType


@dataclass
class ReportMessage:

    """Structured representation of a user report message."""

    user_name: str
    user_location: Tuple[float, float]
    location_name: str
    location_pos: Tuple[float, float]
    report_type: ReportType
    delay_minutes: Optional[int] = None
    trust_score: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "user_name": self.user_name,
            "user_location": {
                "latitude": self.user_location[0],
                "longitude": self.user_location[1]
            },
            "location_name": self.location_name,
            "location_pos": {
                "latitude": self.location_pos[0],
                "longitude": self.location_pos[1]
            },
            "report_type": self.report_type.name,
            "delay_minutes": self.delay_minutes
        }
    
    @classmethod
    def from_json(cls, raw: str) -> 'ReportMessage':
        ...  # TODO: Implement JSON parsing logic

