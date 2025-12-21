from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass
class Request:
    id: int
    user_id: int
    departure: str
    arrival: str
    adults: int
    round_trip: bool
    created_at: datetime
    status: str

    @classmethod
    def from_tuple(cls, data: Tuple) -> "Request":
        """Create Request from tuple with positional mapping"""
        return cls(
            id=data[0],
            user_id=data[1],
            departure=data[2],
            arrival=data[3],
            adults=data[4],
            round_trip=data[5],
            created_at=data[6],
            status=data[7],
        )
