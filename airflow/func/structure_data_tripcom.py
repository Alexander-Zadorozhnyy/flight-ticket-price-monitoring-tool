import re
from datetime import datetime, timedelta
import json


def transform_flight_data(input_data, departure_date: datetime):
    """
    Transform flight data from source format to desired format.

    Args:
        input_data (dict): Original flight data
        departure_date (str): Date in YYYY-MM-DD format for departure

    Returns:
        dict: Transformed flight data
    """

    # Helper function to parse time duration
    def parse_duration(duration_str):
        """Convert duration string like '1h 25m' to total minutes"""
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

    # Helper function to parse price
    def parse_price(price_str):
        """Extract amount and currency from price string like 'RUB 8,270'"""
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
            except:
                amount = None
        else:
            amount = None

        return amount, currency

    # Helper function to extract airport code
    def extract_airport_code(airport_str):
        """Extract IATA code from airport string like 'LED T1'"""
        if not airport_str:
            return None

        # Split by space and take first part (assuming it's the IATA code)
        parts = airport_str.split()
        return parts[0] if parts else None

    # Helper function to create datetime string
    def create_datetime(date: datetime, time_str):
        """Combine date and time into ISO format string"""
        try:
            # Parse time
            dt = datetime.strptime(
                f"{date.year}-{date.month}-{date.day} {time_str}", "%Y-%m-%d %H:%M"
            )
            return dt.isoformat()
        except:
            return None

    # Parse duration
    total_minutes = parse_duration(input_data.get("duration", ""))

    # Parse price
    price_amount, price_currency = parse_price(input_data.get("price", ""))

    # Extract airport codes
    dep_airport = extract_airport_code(input_data.get("departure_airport", ""))
    arr_airport = extract_airport_code(input_data.get("arrival_airport", ""))

    # Create datetime strings
    dep_datetime = create_datetime(departure_date, input_data.get("departure_time", ""))

    # Calculate arrival datetime
    if dep_datetime and total_minutes:
        dep_dt = datetime.fromisoformat(dep_datetime)
        arr_dt = dep_dt + timedelta(minutes=total_minutes)
        arr_datetime = arr_dt.isoformat()
    else:
        arr_datetime = None

    # Parse stops information
    stop_type = input_data.get("stop_type", "").lower()
    stops_count = 0 if stop_type == "nonstop" else 1  # Simplified - adjust as needed
    is_direct = stop_type == "nonstop"

    # Parse baggage information
    baggage_included = input_data.get("baggage_included", False)
    baggage_type = "included" if baggage_included else "not_included"

    # Parse seats information
    seats_left_str = input_data.get("seats_left", "")
    seats_available = False
    seats_left = None

    if seats_left_str:
        # Extract number from string like '<9 left'
        seats_match = re.search(r"(\d+)", seats_left_str)
        if seats_match:
            seats_left = int(seats_match.group(1))
            seats_available = seats_left > 0

    # Map airline names to codes (you'll need to expand this dictionary)
    airline_codes = {
        "Aeroflot": "SU",
        "S7 Airlines": "S7",
        "Ural Airlines": "U6",
        "Pobeda": "DP",
        "Utair": "UT",
        "Rossiya Airlines": "FV",
        "Nordwind Airlines": "N4",
        "Azur Air": "ZF",
        "Red Wings Airlines": "WZ",
        "NordStar": "Y7",
        "Izhavia": "I8",
        "Smartavia": "5N",
        "Yakutia Airlines": "R3",
        "Angara Airlines": "2G",
        "IrAero": "IO",
        "Alrosa": "6R",
        "Vologda Aviation": "KV",
        "RusLine": "7R",
        "Severstal": "D2",
        "Pegas Fly": "EO",
    }

    airline_name = input_data.get("airline", "")
    airline_code = airline_codes.get(
        airline_name, airline_name[:2].upper() if airline_name else None
    )

    # Construct the transformed data
    transformed = {
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

    return transformed


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

    transformed = transform_flight_data(
        input_example, departure_date=datetime(2026, 12, 12)
    )

    with open("output_tripcom.json", "w", encoding="utf-8") as outfile:
        json.dump(transformed, outfile, indent=4)
