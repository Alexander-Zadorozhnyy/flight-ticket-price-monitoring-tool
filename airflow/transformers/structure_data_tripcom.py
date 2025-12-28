import os
from pathlib import Path
import re
from datetime import datetime, timedelta
import sys
from typing import Dict, Any, Optional, Tuple
import json

sys.path.insert(0, os.getcwd())

from transformers.data_transformer import DataTransformer


class TripcomDataTransformer(DataTransformer):
    """Transformer for Trip.com flight data to standardized schema."""

    def __init__(self, airline_codes_file: Optional[str] = None):
        """
        Initialize transformer with airline codes.

        Args:
            airline_codes_file: Path to JSON file with airline code mappings
        """
        super().__init__()
        self.airline_codes = self.load_airline_codes(airline_codes_file)

    def load_airline_codes(self, file_path: Optional[str] = None) -> Dict[str, str]:
        """
        Load airline codes from JSON file.

        Args:
            file_path: Path to JSON file with airline code mappings

        Returns:
            Dictionary mapping airline names to IATA codes
        """
        if not file_path or not Path(file_path).exists():
            print(f"Airline codes file not found: {file_path}. Using empty mapping.")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                airline_codes = json.load(f)

            print(f"Loaded {len(airline_codes)} airline codes from {file_path}")
            return airline_codes

        except Exception as e:
            print(f"Error loading airline codes from {file_path}: {e}")
            return {}

    @staticmethod
    def get_airline_code(airline_name: Optional[str]) -> Optional[str]:
        """
        Safely extract airline code from airline name.

        Handles:
        - None values
        - Multiple airlines separated by commas
        - Whitespace
        - Invalid inputs
        """
        if not airline_name:
            return None

        try:
            # Ensure it's a string
            airline_str = str(airline_name).strip()
            if not airline_str:
                return None

            # Split by comma if multiple airlines
            airlines = [a.strip() for a in airline_str.split(",") if a.strip()]
            if not airlines:
                return None

            # Take the first airline
            first_airline = airlines[0]

            # Try to extract IATA code (2 letters)
            # First, check if it's already a 2-letter code
            if len(first_airline) == 2 and first_airline.isalpha():
                return first_airline.upper()

            # Try to find a 2-letter code in the string
            code_match = re.search(r"\b([A-Z]{2})\b", first_airline.upper())
            if code_match:
                return code_match.group(1)

            # If no code found, return the first two letters of the name
            # (this is a fallback, not always accurate)
            return first_airline[:2].upper() if len(first_airline) >= 2 else None

        except Exception:
            # Return None on any error
            return None

    def structure_flight_output(
        self, flight_dict: Dict[str, Any], departure_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Structure a single flight output.

        Args:
            flight_dict: Flight dictionary from Trip.com
            departure_date: Departure date

        Returns:
            Structured flight dictionary
        """
        # Parse duration
        total_minutes = self.parse_duration(flight_dict.get("duration", ""))

        # Parse price
        price_amount, price_currency = self.parse_price(flight_dict.get("price", ""))

        # Extract airport codes
        dep_airport = self.extract_airport_code(
            flight_dict.get("departure_airport", "")
        )
        arr_airport = self.extract_airport_code(flight_dict.get("arrival_airport", ""))

        # Create datetime strings
        dep_datetime = self.create_datetime(
            departure_date, flight_dict.get("departure_time", "")
        )

        # Calculate arrival datetime
        if dep_datetime and total_minutes:
            dep_dt = datetime.fromisoformat(dep_datetime)
            arr_dt = dep_dt + timedelta(minutes=total_minutes)
            arr_datetime = arr_dt.isoformat()
        else:
            arr_datetime = None

        # Parse stops information
        stop_type = flight_dict.get("stop_type", "").lower()
        stops_count = 0 if stop_type == "nonstop" else 1
        is_direct = stop_type == "nonstop"

        # Parse baggage information
        baggage_included = flight_dict.get("baggage_included", False)
        baggage_type = "included" if baggage_included else "not_included"

        # Parse seats information
        seats_left_str = flight_dict.get("seats_left", "")
        seats_available, seats_left = self.parse_seats_info(seats_left_str)

        # Get airline code
        # Get airline code using enhanced matching
        airline_name = flight_dict.get("airline", "")
        airline_code = self.get_airline_code(airline_name)

        # Construct the structured data
        structured = {
            "airline": airline_code,
            "operating_airlines": [airline_code],  # Same as main airline in this case
            "departure": {"airport": dep_airport, "datetime": dep_datetime},
            "arrival": {"airport": arr_airport, "datetime": arr_datetime},
            "duration": {"total_minutes": total_minutes},
            "stops": {"count": stops_count, "is_direct": is_direct},
            "price": {"amount": price_amount, "currency": price_currency},
            "services": {
                "baggage": baggage_included,
                "baggage_type": baggage_type,
                "seats_available": seats_available,
                "seats_left": seats_left,
            },
        }

        return structured

    @staticmethod
    def parse_duration(duration_str: str) -> Optional[int]:
        """
        Convert duration string like '1h 30m', '1ч 30м', '1 h 30 m' to total minutes.

        Handles various formats:
        - '1h 30m', '1h30m', '1 h 30 m'
        - '1ч 30м', '1ч30м', '1 ч 30 м'
        - '1:30' (1 hour 30 minutes)
        - '90m', '90 мин'
        """
        if not duration_str:
            return None

        duration_str = str(duration_str).strip().lower()

        # Try to parse hours and minutes
        hours = 0
        minutes = 0

        # Handle formats like "1h 30m", "1ч 30м", "1 h 30 m"
        if "h" in duration_str or "ч" in duration_str or "hour" in duration_str:
            # Look for hours - multiple patterns
            patterns = [
                r"(\d+)\s*h",  # 1h
                r"(\d+)\s*ч",  # 1ч
                r"(\d+)\s*hour",  # 1hour
                r"(\d+):(\d+)",  # 1:30
            ]

            for pattern in patterns:
                match = re.search(pattern, duration_str)
                if match:
                    if ":" in pattern:
                        # For pattern like 1:30
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        break
                    else:
                        hours = int(match.group(1))
                        break

        # Handle formats like "1h 30m", "1ч 30м", "1 h 30 m"
        if (
            "m" in duration_str
            or "м" in duration_str
            or "min" in duration_str
            or "мин" in duration_str
        ):
            # Look for minutes - multiple patterns
            patterns = [
                r"(\d+)\s*m(?!\w)",  # 30m (not followed by letter)
                r"(\d+)\s*м(?!\w)",  # 30м (not followed by letter)
                r"(\d+)\s*min",  # 30min
                r"(\d+)\s*мин",  # 30мин
                r"(\d+):(\d+)",  # 1:30 (minutes from colon format)
            ]

            for pattern in patterns:
                match = re.search(pattern, duration_str)
                if match:
                    if ":" in pattern:
                        # Already handled in hours section
                        continue
                    else:
                        minutes = int(match.group(1))
                        break

        # If no hours/minutes markers found, try to parse as total minutes
        if hours == 0 and minutes == 0:
            # Try to extract any number and assume it's minutes
            num_match = re.search(r"(\d+)", duration_str)
            if num_match:
                total = int(num_match.group(1))
                # If it's a large number, assume it's already in minutes
                if total > 60:
                    return total
                # Otherwise assume it's hours
                else:
                    hours = total

        total_minutes = hours * 60 + minutes
        return total_minutes if total_minutes > 0 else None

    @staticmethod
    def parse_price(price_str: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Extract amount and currency from price string.
        """
        if not price_str:
            return None, None

        price_str = str(price_str).strip()

        # Common currency symbols and codes
        currency_patterns = {
            "RUB": r"(?:rub|₽|р\.?|руб\.?)",
            "USD": r"(?:usd|\$|долл\.?)",
            "EUR": r"(?:eur|€|евро?)",
            "GBP": r"(?:gbp|£|фунт\.?)",
        }

        amount = None
        currency = None

        # Try to find currency first
        for currency_code, pattern in currency_patterns.items():
            currency_match = re.search(pattern, price_str, re.IGNORECASE)
            if currency_match:
                currency = currency_code
                # Remove the currency part to extract amount
                price_without_currency = (
                    price_str[: currency_match.start()]
                    + price_str[currency_match.end() :]
                )
                price_without_currency = price_without_currency.strip()
                break

        # If no currency found with patterns, try to find common currency codes
        if not currency:
            # Look for 3-letter currency code at beginning or end
            currency_match = re.search(r"\b([A-Z]{3})\b", price_str)
            if currency_match:
                currency = currency_match.group(1)
                # Remove currency code
                price_without_currency = price_str.replace(
                    currency_match.group(0), ""
                ).strip()
            else:
                # Try to find currency symbol
                symbol_match = re.search(r"([₽€$£])", price_str)
                if symbol_match:
                    symbol = symbol_match.group(1)
                    symbol_to_currency = {
                        "₽": "RUB",
                        "€": "EUR",
                        "$": "USD",
                        "£": "GBP",
                    }
                    currency = symbol_to_currency.get(symbol, symbol)
                    price_without_currency = price_str.replace(symbol, "").strip()
                else:
                    # No currency found, use the whole string for amount
                    price_without_currency = price_str

        # Extract numeric amount
        # Handle various formats: 7,825; 7825; 120.50; 99.99
        amount_patterns = [
            r"[\d,]+\.\d+",  # 120.50, 99.99
            r"[\d,]+",  # 7,825, 7825
        ]

        for pattern in amount_patterns:
            amount_match = re.search(pattern, price_without_currency)
            if amount_match:
                amount_str = amount_match.group(0)
                try:
                    # Remove thousand separators
                    amount_str = amount_str.replace(",", "")
                    # Convert to integer (multiply by 100 for cents if needed)
                    if "." in amount_str:
                        # Handle decimal amounts
                        amount = int(float(amount_str))
                    else:
                        amount = int(amount_str)
                    break
                except (ValueError, AttributeError):
                    continue

        # If still no amount found, try to extract any number
        if amount is None:
            num_match = re.search(r"\d+", price_without_currency)
            if num_match:
                try:
                    amount = int(num_match.group(0))
                except ValueError:
                    amount = None

        # Default currency if not found
        if not currency and amount is not None:
            # Try to infer from context or use default
            if (
                "₽" in price_str
                or "р" in price_str.lower()
                or "руб" in price_str.lower()
            ):
                currency = "RUB"
            elif "€" in price_str or "евр" in price_str.lower():
                currency = "EUR"
            elif "$" in price_str or "долл" in price_str.lower():
                currency = "USD"
            elif "£" in price_str or "фунт" in price_str.lower():
                currency = "GBP"

        return amount, currency

    @staticmethod
    def extract_airport_code(airport_str: str) -> Optional[str]:
        """Extract IATA code from airport string like 'LED T1'."""
        if not airport_str:
            return None

        # Split by space and take first part (assuming it's the IATA code)
        parts = airport_str.split()
        return parts[0] if parts else None

    @staticmethod
    def create_datetime(base_date: datetime, time_str: str) -> Optional[str]:
        """Combine date and time into ISO format string."""
        try:
            # Parse time
            dt = datetime.strptime(
                f"{base_date.year}-{base_date.month}-{base_date.day} {time_str}",
                "%Y-%m-%d %H:%M",
            )
            return dt.isoformat()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_seats_info(seats_left_str: str) -> Tuple[bool, Optional[int]]:
        """Parse seats information from string like '<9 left'."""
        seats_available = False
        seats_left = None

        if seats_left_str:
            # Extract number from string like '<9 left'
            seats_match = re.search(r"(\d+)", seats_left_str)
            if seats_match:
                seats_left = int(seats_match.group(1))
                seats_available = seats_left > 0

        return seats_available, seats_left


# Example usage:
if __name__ == "__main__":
    input_example = {
        "airline": "Aeroflot",
        "departure_time": "19:30",
        "departure_airport": "LED T1",
        "arrival_time": "20:55",
        "arrival_airport": "SVO B",
        "duration": "1h 30m",
        "stop_type": "Nonstop",
        "price": "RUB 8,270",
        "baggage_included": True,
        "seats_left": "<9 left",
    }

    airline_file = "utils/airline_codes_simple.json"
    transformer = TripcomDataTransformer(airline_codes_file=airline_file)

    # Test with example data
    test_flights = [
        {
            "airline": "Pobeda",
            "departure_time": "08:05",
            "departure_airport": "SVO D",
            "arrival_time": "09:35",
            "arrival_airport": "LED T1",
            "duration": "1h 30m",
            "stop_type": "Nonstop",
            "price": "RUB 4,808",
            "baggage_included": True,
            "seats_left": "<9 left",
        },
        {
            "airline": None,
            "departure_time": None,
            "departure_airport": None,
            "arrival_time": None,
            "arrival_airport": None,
            "duration": None,
            "stop_type": None,
            "price": None,
            "baggage_included": False,
            "seats_left": None,
        },
    ]

    # Transform flights
    transformed, q = transformer.structure_flight_output_list(
        test_flights, departure_date=datetime(2026, 12, 12)
    )

    print("Transformed flights:")
    for i, flight in enumerate(transformed):
        print(f"\nFlight {i + 1}:")
        print(json.dumps(flight, indent=2, ensure_ascii=False))
        
    print(q.to_dict())
