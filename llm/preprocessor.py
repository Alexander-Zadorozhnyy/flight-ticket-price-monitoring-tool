from datetime import date
from enum import Enum
import re
from mistralai import Mistral
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import json


class WeekDay(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class TravelType(str, Enum):
    ROUND_TRIP = "round_trip"
    ONE_WAY = "one_way"
    MULTI_CITY = "multi_city"


class FlightRequest(BaseModel):
    """Main model for flight monitoring request"""

    # Core travel information
    origin: str = Field(
        ...,
        description="Departure city or airport in English (e.g., 'Moscow' or 'SVO')",
    )
    destination: str = Field(
        ..., description="Arrival city or airport in English (e.g., 'London' or 'LHR')"
    )

    # Date range
    start_date: date = Field(..., description="Earliest departure date")
    end_date: date = Field(..., description="Latest departure date")

    # Trip type
    travel_type: TravelType = Field(
        default=TravelType.ROUND_TRIP, description="Type of travel"
    )

    # Flexible options
    flexible_days: int = Field(
        default=0, ge=0, le=14, description="Flexibility in days (+/-)"
    )

    # Preferred days
    departure_days: Optional[List[WeekDay]] = Field(
        default=None, description="Preferred departure days of week"
    )
    return_days: Optional[List[WeekDay]] = Field(
        default=None, description="Preferred return days of week (for round trips)"
    )

    # Trip duration (for round trips)
    trip_duration_min: Optional[int] = Field(
        default=None, ge=1, le=365, description="Minimum trip duration in days"
    )
    trip_duration_max: Optional[int] = Field(
        default=None, ge=1, le=365, description="Maximum trip duration in days"
    )

    # Budget constraints (optional)
    budget_min: Optional[float] = Field(
        default=None, ge=0, description="Minimum acceptable price in RUB"
    )
    budget_max: Optional[float] = Field(
        default=None, ge=0, description="Maximum acceptable price in RUB"
    )

    # Airline preferences
    preferred_airlines: Optional[List[str]] = Field(
        default=None, description="Preferred airline codes (e.g., ['SU', 'S7'])"
    )
    excluded_airlines: Optional[List[str]] = Field(
        default=None, description="Airlines to exclude"
    )

    # Stop preferences
    max_stops: int = Field(default=2, ge=0, le=4, description="Maximum number of stops")
    direct_only: bool = Field(default=False, description="Only direct flights")

    # Baggage requirements
    baggage_required: bool = Field(
        default=True, description="Baggage included required"
    )

    # Monitoring parameters
    monitoring_duration_days: int = Field(
        default=30, ge=1, le=365, description="How long to monitor prices"
    )
    alert_threshold_percent: float = Field(
        default=10.0, ge=0, le=100, description="Price drop percentage to trigger alert"
    )

    # Metadata
    user_email: Optional[str] = Field(default=None, description="Email for alerts")
    request_source: str = Field(
        default="user_chat", description="Source of the request"
    )

    # Normalized fields (to be filled by processing)
    origin_iata: Optional[str] = Field(
        default=None, description="Normalized IATA code for origin"
    )
    destination_iata: Optional[str] = Field(
        default=None, description="Normalized IATA code for destination"
    )
    origin_city: Optional[str] = Field(default=None, description="City name for origin")
    destination_city: Optional[str] = Field(
        default=None, description="City name for destination"
    )

    @field_validator("origin", "destination")
    @classmethod
    def validate_location_format(cls, v: str) -> str:
        """Validate location format"""
        if not v or len(v.strip()) < 2:
            raise ValueError(f"Location must be at least 2 characters: {v}")

        # Convert to title case for cities
        v = v.strip().title()

        # Check if it looks like an IATA code (3 letters)
        if re.match(r"^[A-Z]{3}$", v.upper()):
            return v.upper()

        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Ensure end_date is after start_date"""
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("end_date must be after start_date")

        # Limit to 1 year in future
        max_date = date.today().replace(year=date.today().year + 1)
        if v > max_date:
            raise ValueError(f"Date cannot be more than 1 year in the future")

        return v

    @field_validator("budget_min", "budget_max", mode="before")
    @classmethod
    def validate_budget(cls, v):
        """Handle budget validation"""
        if v is not None and v <= 0:
            raise ValueError("Budget must be positive")
        return v

    @field_validator("preferred_airlines", "excluded_airlines")
    @classmethod
    def validate_airline_codes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate airline codes are 2-letter IATA codes"""
        if v is None:
            return v

        validated = []
        for code in v:
            clean_code = code.strip().upper()
            if not re.match(r"^[A-Z0-9]{2}$", clean_code):
                raise ValueError(f"Invalid airline code format: {code}")
            validated.append(clean_code)

        return validated

    def to_monitoring_config(self) -> Dict[str, Any]:
        """Convert to monitoring configuration"""
        return {
            "origin": self.origin_iata or self.origin,
            "destination": self.destination_iata or self.destination,
            "date_range": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
                "flexible_days": self.flexible_days,
            },
            "preferences": {
                "departure_days": [d.value for d in self.departure_days]
                if self.departure_days
                else None,
                "return_days": [d.value for d in self.return_days]
                if self.return_days
                else None,
                "trip_duration": {
                    "min": self.trip_duration_min,
                    "max": self.trip_duration_max,
                }
                if self.trip_duration_min or self.trip_duration_max
                else None,
                "budget": {"min": self.budget_min, "max": self.budget_max}
                if self.budget_min or self.budget_max
                else None,
                "airlines": {
                    "preferred": self.preferred_airlines,
                    "excluded": self.excluded_airlines,
                },
                "stops": {"max": self.max_stops, "direct_only": self.direct_only},
                "baggage_required": self.baggage_required,
            },
            "monitoring": {
                "duration_days": self.monitoring_duration_days,
                "alert_threshold_percent": self.alert_threshold_percent,
            },
        }

    class Config:
        json_schema_extra = {
            "example": {
                "origin": "Moscow",
                "destination": "London",
                "start_date": "2024-12-01",
                "end_date": "2024-12-31",
                "travel_type": "round_trip",
                "flexible_days": 3,
                "departure_days": ["Friday", "Saturday"],
                "return_days": ["Sunday"],
                "trip_duration_min": 5,
                "trip_duration_max": 10,
                "budget_max": 50000.0,
                "preferred_airlines": ["SU", "BA"],
                "max_stops": 1,
                "monitoring_duration_days": 30,
                "alert_threshold_percent": 15.0,
            }
        }


SYSTEM_PROMPT = """
You are a flight monitoring classifier assistant. Your task is to analyze user requests and determine if they are asking to find and monitor flight tickets.

CRITICAL INSTRUCTIONS:
1. ONLY classify as a flight monitoring request if ALL these conditions are met:
   - User specifies origin AND destination locations
   - User specifies dates or date ranges
   - User explicitly wants to track/find/book flights or monitor prices

2. If ANY of the following, it is NOT a flight monitoring request:
   - Questions about weather, hotels, visas, or general travel info
   - Requests for historical data only (not current/future monitoring)
   - General conversations about travel without specific flight details
   - Test messages or greetings

3. EXTRACTION RULES:
   - Extract locations in ENGLISH format for IATA mapping
   - Convert dates to YYYY-MM-DD format
   - Normalize city names: "Moscow" not "Moskva", "London" not "Лондон"
   - For date ranges: Extract both start and end dates
   - For flexible dates: Extract ± days if mentioned

4. UNCERTAIN CASES:
   - If ambiguous, ask clarifying questions
   - If missing critical info (dates/locations), request it
   - DO NOT guess or assume missing information

5. OUTPUT FORMAT:
   You MUST output a JSON object with this exact structure:
   {
     "is_flight_request": boolean,
     "confidence": float (0.0 to 1.0),
     "flight_data": FlightRequest or null,
     "missing_info": list of missing fields,
     "clarification_questions": list of questions if needed
   }

Example positive classification:
User: "I want to track flights from Paris to Tokyo between December 10-20, 2024"
Output: {
  "is_flight_request": true,
  "confidence": 0.95,
  "flight_data": {
    "origin": "Paris",
    "destination": "Tokyo",
    "start_date": "2024-12-10",
    "end_date": "2024-12-20",
    ...
  },
  "missing_info": [],
  "clarification_questions": []
}

Example negative classification:
User: "What's the weather in Tokyo?"
Output: {
  "is_flight_request": false,
  "confidence": 0.99,
  "flight_data": null,
  "missing_info": [],
  "clarification_questions": []
}
"""

USER_PROMPT_TEMPLATE = """
Пользователь хочет отслеживать изменения цен на авиабилеты.

ИНСТРУКЦИИ ПО ОБРАБОТКЕ РУССКОГО ВВОДА:
1. Переведи все локации на английский язык:
   - "Москва" → "Moscow"
   - "Санкт-Петербург" → "Saint Petersburg"
   - "Лондон" → "London"

2. Обработай даты в русском формате:
   - "15 декабря 2026" → "2026-12-15"
   - "с 10 по 20 января" → start_date: "2026-01-10", end_date: "2026-01-20"
   - "в феврале" → calculate start_date: "2026-02-01", end_date: "2026-02-29"

3. Дни недели на русском → английский:
   - "понедельник" → "Monday"
   - "вторник" → "Tuesday"
   - "среда" → "Wednesday"
   - "четверг" → "Thursday"
   - "пятница" → "Friday"
   - "суббота" → "Saturday"
   - "воскресенье" → "Sunday"

4. Ключевые фразы для определения мониторинга:
   - "отслеживать цены" → flight monitoring
   - "найти билеты" → flight search
   - "следить за ценами" → price tracking
   - "уведомить когда подешевеет" → price alert

ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС:
{user_input}

ТРЕБОВАНИЯ К ИЗВЛЕЧЕНИЮ:
- отправная и конечная точка в формате аэропорт или город. Выдай на английском языке в официальном формате, для mapping'а в IATA коды
- в период с N месяц/число до M месяц/число
- вылет в определенные дни недели (опционально)
- прилет в определенные дни недели (опционально)
- желаемый срок поездки (опционально +- K дней)

ВЫВЕДИ ТОЛЬКО JSON ОБЪЕКТ БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА.
"""

request = "Хочу отслеживать цены на билеты из Москвы в Лондон с 10 декабря, вылет по пятницам"

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    },
    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(user_input=request)},
]

api_key = "l56sC2ktV2UhuxoizLMsxcDjcBmvj4mi"


client = Mistral(api_key=api_key)

chat_response = client.chat.complete(
    model="mistral-small-latest",
    messages=messages,
    response_format={"type": "json_object"},
    temperature=0.1,
)

# Parse the response as structured data
result = json.loads(chat_response.choices[0].message.content)

print(result)
