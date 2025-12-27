from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re


class KypibiletDataTransformer:
    def structure_flight_output_list(
        self, flights: List[Dict[str, Any]], departure_date
    ):
        result = []

        for flight in flights:
            try:
                structured_output = self.structure_flight_output(
                    flight_dict=flight, departure_date=departure_date
                )
                if structured_output:
                    result.append(structured_output)
            except Exception as e:
                import traceback

                traceback.print_exc()
                print(f"Error while transforming flight data: {str(e)}")
                continue

        return result

    # Function to create structured output with specific fields
    def structure_flight_output(
        self, flight_dict: Dict[str, Any], departure_date
    ) -> Optional[Dict[str, Any]]:
        """
        Create a clean, structured output with only essential fields.
        """
        try:
            normalized = self.normalize_flight_dict(flight_dict, departure_date)
        except Exception:
            return None

        structured = {
            # Basic flight info
            "airline": normalized["main_airline"],
            "operating_airlines": normalized["operating_airlines"],
            # Route info
            "departure": {
                "airport": normalized.get("departure_airport"),
                "datetime": normalized.get("departure_datetime").isoformat(),  # type: ignore
            },
            "arrival": {
                "airport": normalized.get("arrival_airport"),
                "datetime": normalized.get("arrival_datetime").isoformat(),  # type: ignore
            },
            # Flight details
            "duration": {
                "total_minutes": normalized["duration_total_minutes"],
            },
            # Stop info
            "stops": {
                "count": normalized["stops_count"],
                "is_direct": normalized["is_direct"],
            },
            # Price info
            "price": {
                "amount": normalized["price_numeric"],
                "currency": normalized["currency"],
            },
            # Additional services
            "services": {
                "baggage": normalized["baggage_included"],
                "baggage_type": normalized["baggage_type"],
                "seats_available": normalized["seats_available"],
                "seats_left": normalized["seats_left"],
            },
        }

        return structured

    # Function to process multiple flights
    def normalize_flight_list(
        self, flight_dicts: List[Dict[str, Any]], departure_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Normalize a list of flight dictionaries.
        """
        return [
            self.normalize_flight_dict(flight, departure_date)
            for flight in flight_dicts
        ]

    def normalize_flight_dict(
        self, flight_dict: Dict[str, Any], departure_date: datetime
    ) -> Dict[str, Any]:
        """
        Transform flight dictionary into a normalized/standardized format.

        Args:
            flight_dict: Raw flight data dictionary

        Returns:
            Normalized flight dictionary with consistent data types and structure
        """
        normalized = {}

        # 1. Parse airlines
        airlines = flight_dict.get("airline", "")
        if airlines:
            # Split by comma and clean up
            airline_list = [
                airline.strip() for airline in airlines.split(",") if airline.strip()
            ]
            normalized["airlines"] = airline_list
            normalized["main_airline"] = airline_list[0] if airline_list else None
            normalized["operating_airlines"] = (
                airline_list[1:] if len(airline_list) > 1 else []
            )
        else:
            normalized["airlines"] = []
            normalized["main_airline"] = None
            normalized["operating_airlines"] = []

        # 2. Parse times
        departure_time_str = flight_dict.get("departure_time", "")
        arrival_time_str = flight_dict.get("arrival_time", "")
        departure_airport = flight_dict.get("departure_airport", "")
        arrival_airport = flight_dict.get("arrival_airport", "")

        # Parse departure datetime
        departure_dt = None
        if departure_time_str:
            try:
                hour, minute = map(int, departure_time_str.split(":"))
                departure_dt = datetime(
                    year=departure_date.year,
                    month=departure_date.month,
                    day=departure_date.day,
                    hour=hour,
                    minute=minute,
                )
            except (ValueError, AttributeError):
                departure_dt = None

        # Parse duration to calculate arrival datetime
        duration_str = flight_dict.get("duration", "")
        hours = 0
        minutes = 0

        if duration_str:
            hour_match = re.search(r"(\d+)\s*ч", duration_str)
            if hour_match:
                hours = int(hour_match.group(1))

            minute_match = re.search(r"(\d+)\s*м", duration_str)
            if minute_match:
                minutes = int(minute_match.group(1))

        total_minutes = hours * 60 + minutes
        normalized["duration_minutes"] = total_minutes

        # Calculate arrival datetime
        arrival_dt = None
        if departure_dt and total_minutes > 0:
            arrival_dt = departure_dt + timedelta(minutes=total_minutes)
        elif arrival_time_str:
            # Try to parse arrival time directly
            try:
                hour, minute = map(int, arrival_time_str.split(":"))
                arrival_dt = datetime(
                    year=departure_date.year,
                    month=departure_date.month,
                    day=departure_date.day,
                    hour=hour,
                    minute=minute,
                )
                # If arrival time is earlier than departure time, assume next day
                if arrival_dt < departure_dt:  # type: ignore
                    arrival_dt += timedelta(days=1)
            except (ValueError, AttributeError):
                arrival_dt = None

        # Store datetime objects
        normalized["departure_datetime"] = departure_dt
        normalized["arrival_datetime"] = arrival_dt

        # 3. Parse airports
        normalized["departure_airport"] = flight_dict.get("departure_airport", "")
        normalized["arrival_airport"] = flight_dict.get("arrival_airport", "")

        # 4. Parse duration
        duration_str = flight_dict.get("duration", "")
        normalized["duration_str"] = duration_str

        # Extract hours and minutes from duration string
        hours = 0
        minutes = 0

        if duration_str:
            # Find hours
            hour_match = re.search(r"(\d+)\s*ч", duration_str)
            if hour_match:
                hours = int(hour_match.group(1))

            # Find minutes
            minute_match = re.search(r"(\d+)\s*м", duration_str)
            if minute_match:
                minutes = int(minute_match.group(1))

        normalized["duration_hours"] = hours
        normalized["duration_minutes"] = minutes
        normalized["duration_total_minutes"] = hours * 60 + minutes

        # 5. Parse stop information
        stop_type = flight_dict.get("stop_type", "")
        normalized["stop_type"] = stop_type
        normalized["stops_count"] = 0
        normalized["is_direct"] = (
            "без пересадок" in stop_type.lower() or "прямой" in stop_type.lower()
        )

        # Try to extract number of stops
        if stop_type and not normalized["is_direct"]:
            stop_match = re.search(r"(\d+)\s*(пересад|стоп)", stop_type.lower())
            if stop_match:
                normalized["stops_count"] = int(stop_match.group(1))

        # 6. Parse price
        price_str = flight_dict.get("price", "0 ₽")
        normalized["price_str"] = price_str

        # Extract numeric price
        price_match = re.search(r"([\d\s]+)", price_str.replace("₽", "").strip())
        if price_match:
            price_number = int(price_match.group(1).replace(" ", ""))
        else:
            price_number = 0

        normalized["price_numeric"] = price_number
        normalized["currency"] = "RUB" if "₽" in price_str else "Unknown"

        # 7. Parse baggage information
        baggage_included = flight_dict.get("baggage_included", False)
        normalized["baggage_included"] = bool(baggage_included)
        normalized["baggage_type"] = "included" if baggage_included else "not_included"

        # 8. Parse seats left
        seats_left = flight_dict.get("seats_left", None)
        normalized["seats_left"] = seats_left
        normalized["seats_available"] = seats_left is not None and seats_left > 0

        # 9. Calculate arrival date (if departure date is known)
        # This assumes we know the departure date separately
        if departure_dt and arrival_dt:
            normalized["flight_date"] = departure_dt.date()
            normalized["arrival_date"] = arrival_dt.date()
            normalized["overnight"] = departure_dt.date() != arrival_dt.date()

        return normalized


# Example usage and testing
if __name__ == "__main__":
    # Example flight data
    raw_flight = {
        "airline": "SU,FV,SU",
        "departure_time": "10:00",
        "departure_airport": "LED",
        "arrival_time": "11:25",
        "arrival_airport": "SVO",
        "duration": "1ч 25м",
        "stop_type": "Без пересадок",
        "price": "7 833 ₽",
        "baggage_included": False,
        "seats_left": None,
    }

    tr = KypibiletDataTransformer()

    # Test structured output
    structured = tr.structure_flight_output(
        raw_flight, departure_date=datetime(2026, 1, 10)
    )
    print(f"Structured output: {structured}")

    # import json

    # with open("output.json", "w", encoding="utf-8") as outfile:
    #     json.dump(structured, outfile, indent=4)


# def compare_flights(flight1: Dict[str, Any], flight2: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Compare two normalized flights.
#     """
#     normalized1 = (
#         normalize_flight_dict(flight1) if "airlines" not in flight1 else flight1
#     )
#     normalized2 = (
#         normalize_flight_dict(flight2) if "airlines" not in flight2 else flight2
#     )

#     comparison = {
#         "price_difference": normalized1["price_numeric"] - normalized2["price_numeric"],
#         "duration_difference": normalized1["duration_total_minutes"]
#         - normalized2["duration_total_minutes"],
#         "is_cheaper": normalized1["price_numeric"] < normalized2["price_numeric"],
#         "is_faster": normalized1["duration_total_minutes"]
#         < normalized2["duration_total_minutes"],
#         "has_baggage_advantage": normalized1["baggage_included"]
#         and not normalized2["baggage_included"],
#         "same_airline": normalized1["main_airline"] == normalized2["main_airline"],
#     }

#     return comparison
