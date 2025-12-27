# import re
# from datetime import datetime, timedelta
# import json


# def transform_flight_data(input_data, departure_date: datetime):
#     """
#     Transform flight data from source format to desired format.

#     Args:
#         input_data (dict): Original flight data
#         departure_date (str): Date in YYYY-MM-DD format for departure

#     Returns:
#         dict: Transformed flight data
#     """

#     # Helper function to parse time duration
#     def parse_duration(duration_str):
#         """Convert duration string like '1h 25m' to total minutes"""
#         hours = 0
#         minutes = 0

#         if "h" in duration_str:
#             hours_match = re.search(r"(\d+)h", duration_str)
#             if hours_match:
#                 hours = int(hours_match.group(1))

#         if "m" in duration_str:
#             minutes_match = re.search(r"(\d+)m", duration_str)
#             if minutes_match:
#                 minutes = int(minutes_match.group(1))

#         return hours * 60 + minutes

#     # Helper function to parse price
#     def parse_price(price_str):
#         """Extract amount and currency from price string like 'RUB 8,270'"""
#         if not price_str:
#             return None, None

#         # Extract currency code (assuming it's at the beginning)
#         currency_match = re.match(r"^([A-Z]{3})", price_str)
#         currency = currency_match.group(1) if currency_match else None

#         # Extract numeric value, removing thousand separators
#         amount_match = re.search(r"[\d,]+(?:\.\d+)?", price_str)
#         if amount_match:
#             amount_str = amount_match.group(0).replace(",", "")
#             try:
#                 amount = int(float(amount_str))
#             except:
#                 amount = None
#         else:
#             amount = None

#         return amount, currency

#     # Helper function to extract airport code
#     def extract_airport_code(airport_str):
#         """Extract IATA code from airport string like 'LED T1'"""
#         if not airport_str:
#             return None

#         # Split by space and take first part (assuming it's the IATA code)
#         parts = airport_str.split()
#         return parts[0] if parts else None

#     # Helper function to create datetime string
#     def create_datetime(date: datetime, time_str):
#         """Combine date and time into ISO format string"""
#         try:
#             # Parse time
#             dt = datetime.strptime(
#                 f"{date.year}-{date.month}-{date.day} {time_str}", "%Y-%m-%d %H:%M"
#             )
#             return dt.isoformat()
#         except:
#             return None

#     # Parse duration
#     total_minutes = parse_duration(input_data.get("duration", ""))

#     # Parse price
#     price_amount, price_currency = parse_price(input_data.get("price", ""))

#     # Extract airport codes
#     dep_airport = extract_airport_code(input_data.get("departure_airport", ""))
#     arr_airport = extract_airport_code(input_data.get("arrival_airport", ""))

#     # Create datetime strings
#     dep_datetime = create_datetime(departure_date, input_data.get("departure_time", ""))

#     # Calculate arrival datetime
#     if dep_datetime and total_minutes:
#         dep_dt = datetime.fromisoformat(dep_datetime)
#         arr_dt = dep_dt + timedelta(minutes=total_minutes)
#         arr_datetime = arr_dt.isoformat()
#     else:
#         arr_datetime = None

#     # Parse stops information
#     stop_type = input_data.get("stop_type", "").lower()
#     stops_count = 0 if stop_type == "nonstop" else 1  # Simplified - adjust as needed
#     is_direct = stop_type == "nonstop"

#     # Parse baggage information
#     baggage_included = input_data.get("baggage_included", False)
#     baggage_type = "included" if baggage_included else "not_included"

#     # Parse seats information
#     seats_left_str = input_data.get("seats_left", "")
#     seats_available = False
#     seats_left = None

#     if seats_left_str:
#         # Extract number from string like '<9 left'
#         seats_match = re.search(r"(\d+)", seats_left_str)
#         if seats_match:
#             seats_left = int(seats_match.group(1))
#             seats_available = seats_left > 0

#     # Map airline names to codes (you'll need to expand this dictionary)
#     airline_codes = {
#         "Aeroflot": "SU",
#         "S7 Airlines": "S7",
#         "Ural Airlines": "U6",
#         "Pobeda": "DP",
#         "Utair": "UT",
#         "Rossiya Airlines": "FV",
#         "Nordwind Airlines": "N4",
#         "Azur Air": "ZF",
#         "Red Wings Airlines": "WZ",
#         "NordStar": "Y7",
#         "Izhavia": "I8",
#         "Smartavia": "5N",
#         "Yakutia Airlines": "R3",
#         "Angara Airlines": "2G",
#         "IrAero": "IO",
#         "Alrosa": "6R",
#         "Vologda Aviation": "KV",
#         "RusLine": "7R",
#         "Severstal": "D2",
#         "Pegas Fly": "EO",
#     }

#     airline_name = input_data.get("airline", "")
#     airline_code = airline_codes.get(
#         airline_name, airline_name[:2].upper() if airline_name else None
#     )

#     # Construct the transformed data
#     transformed = {
#         "airline": airline_code,
#         "operating_airlines": [airline_code],  # Same as main airline in this case
#         "departure": {"airport": dep_airport, "datetime": dep_datetime},
#         "arrival": {"airport": arr_airport, "datetime": arr_datetime},
#         "duration": {"total_minutes": total_minutes},
#         "stops": {"count": stops_count, "is_direct": is_direct},
#         "price": {"amount": price_amount, "currency": price_currency},
#         "services": {
#             "baggage": baggage_included,
#             "baggage_type": baggage_type,
#             "seats_available": seats_available,
#             "seats_left": seats_left,
#         },
#     }

#     return transformed


from pathlib import Path
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json


class TripcomDataTransformer:
    """Transformer for Trip.com flight data to standardized schema."""

    def __init__(self, airline_codes_file: str = None):
        """
        Initialize transformer with airline codes.

        Args:
            airline_codes_file: Path to JSON file with airline code mappings
        """
        self.airline_codes = self.load_airline_codes(airline_codes_file)

    def load_airline_codes(self, file_path: str = None) -> Dict[str, str]:
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

    def get_airline_code(self, airline_name: str) -> Optional[str]:
        """
        Get IATA code for airline name using multiple matching strategies.

        Args:
            airline_name: Name of the airline

        Returns:
            IATA code or None if not found
        """
        if not airline_name:
            return None

        # Clean the airline name
        clean_name = airline_name.strip()

        # Try exact match in loaded airline codes
        if clean_name in self.airline_codes:
            return self.airline_codes[clean_name]

        # Try partial matching (case-insensitive)
        for name, code in self.airline_codes.items():
            if clean_name.lower() == name.lower():
                return code

        # Try removing common suffixes
        suffixes_to_remove = [" Airlines", " Air", " Aviation", " Company", " Lines"]
        base_name = clean_name
        for suffix in suffixes_to_remove:
            base_name = base_name.replace(suffix, "")

        if base_name in self.airline_codes:
            return self.airline_codes[base_name]

        # If no match found, try to extract code from name
        if len(clean_name) >= 2:
            # Try to see if the first two letters might be a code
            potential_code = clean_name[:2].upper()
            if potential_code.isalpha() and len(potential_code) == 2:
                return potential_code

        return None

    @staticmethod
    def parse_duration(duration_str: str) -> int:
        """Convert duration string like '1h 25m' to total minutes."""
        hours = 0
        minutes = 0

        if "h" in duration_str:
            hours_match = re.search(r"(\d+)h", duration_str)
            if hours_match:
                hours = int(hours_match.group(1))

        if "m" in duration_str:
            minutes_match = re.search(r"(\d+)m", duration_str)
            if minutes_match:
                minutes = int(minutes_match.group(1))

        return hours * 60 + minutes

    @staticmethod
    def parse_price(price_str: str) -> Tuple[Optional[int], Optional[str]]:
        """Extract amount and currency from price string like 'RUB 8,270'."""
        if not price_str:
            return None, None

        # Extract currency code (assuming it's at the beginning)
        currency_match = re.match(r"^([A-Z]{3})", price_str)
        currency = currency_match.group(1) if currency_match else None

        # Extract numeric value, removing thousand separators
        amount_match = re.search(r"[\d,]+(?:\.\d+)?", price_str)
        if amount_match:
            amount_str = amount_match.group(0).replace(",", "")
            try:
                amount = int(float(amount_str))
            except ValueError:
                amount = None
        else:
            amount = None

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

    def structure_flight_output_list(
        self, flights: List[Dict[str, Any]], departure_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Structure a list of flight outputs.

        Args:
            flights: List of flight dictionaries from Trip.com
            departure_date: Departure date

        Returns:
            List of structured flight dictionaries
        """
        return [
            self.structure_flight_output(flight, departure_date) for flight in flights
        ]

    def structure_flight_output(
        self, flight_dict: Dict[str, Any], departure_date: datetime
    ) -> Dict[str, Any]:
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


# Example usage:
if __name__ == "__main__":
    input_example = {
        "airline": "Aeroflot",
        "departure_time": "19:30",
        "departure_airport": "LED T1",
        "arrival_time": "20:55",
        "arrival_airport": "SVO B",
        "duration": "1h 25m",
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
            "airline": "Aeroflot",
            "departure_time": "19:30",
            "departure_airport": "LED T1",
            "arrival_time": "20:55",
            "arrival_airport": "SVO B",
            "duration": "1h 25m",
            "stop_type": "Nonstop",
            "price": "RUB 8,270",
            "baggage_included": True,
            "seats_left": "<9 left",
        },
        {
            "airline": "S7 Airlines",
            "departure_time": "15:45",
            "departure_airport": "DME",
            "arrival_time": "18:20",
            "arrival_airport": "AER",
            "duration": "2h 35m",
            "stop_type": "Nonstop",
            "price": "RUB 12,450",
            "baggage_included": True,
            "seats_left": "<5 left",
        },
    ]

    # Transform flights
    transformed = transformer.structure_flight_output_list(
        test_flights, departure_date=datetime(2026, 12, 12)
    )

    print("Transformed flights:")
    for i, flight in enumerate(transformed):
        print(f"\nFlight {i + 1}:")
        print(json.dumps(flight, indent=2, ensure_ascii=False))
