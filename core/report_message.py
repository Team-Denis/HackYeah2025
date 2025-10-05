
from dataclasses import dataclass
from typing import Tuple, Optional, Any
from db import ReportType
import json


@dataclass
class ReportMessage:

    """Structured representation of a user report message."""

    user_name: str
    user_location: Tuple[float, float]
    location_name: str
    location_pos: Tuple[float, float]
    report_type: ReportType
    delay_minutes: Optional[int] = None
    
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

        """Creates a ReportMessage instance from a JSON string."""
        
        data: Any = json.loads(raw)
        
        return cls(
            user_name=data.get('user_name'),
            user_location=(
                data.get('user_location')[0],
                data.get('user_location')[1]
            ),
            location_name=data.get('location_name'),
            location_pos=(
                data.get('location_pos')[0],
                data.get('location_pos')[1]
            ),
            report_type=ReportType(data.get('report_type')),
            delay_minutes=data.get('delay_minutes')
        )

