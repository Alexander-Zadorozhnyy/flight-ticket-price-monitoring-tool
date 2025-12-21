# link for aviasales https://www.aviasales.ru/search/MOW1801LED1?t=DP17687343001768739700000090VKOLED_a64f6f4ca5f0e7f87545e6607592fc6d_3868&search_date=01122025&expected_price_uuid=5b13adee-e87b-4e02-a285-6c07eccc1603&expected_price_source=share&expected_price_currency=usd&expected_price=50
# Special offers https://api.travelpayouts.com/aviasales/v3/get_special_offers?origin=LED&destination=CAN&locale=en&token=c228f38c19918db6a62df3869bd8bb2a
# Logos http://pics.avs.io/width/height/iata.png
# get currency http://yasen.aviasales.com/adaptors/currency.json

import os
from typing import Any, Dict, Optional
import json

from dotenv import load_dotenv
import httpx


class TravelPayoutsClient:
    """
    Client class for interacting with TravelPayouts API.
    """

    def __init__(
        self,
        token: str,
        currency: str = "rub",
        api_request_timeout: int = 30,
    ):
        """
        Initialize TravelPayouts client.

        Args:
            token: Your API token
            base_url: Base URL for the API (default: "http://api.travelpayouts.com/v2")
        """
        self.token = token
        self.base_url_v2 = "http://api.travelpayouts.com/v2"
        self.base_url_v3 = "https://api.travelpayouts.com/aviasales/v3"
        self.currency = currency.lower()
        self.api_request_timeout = api_request_timeout

    def get_monthly_prices(
        self,
        origin: str,
        destination: str,
        month: str,
        show_to_affiliates: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get monthly flight price matrix.

        Args:
            origin: Origin airport IATA code
            destination: Destination airport IATA code
            month: Month in YYYY-MM-DD format
            show_to_affiliates: Whether to show prices to affiliates (default: True)
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Dictionary containing API response
        """
        if not self.token:
            raise ValueError("API token is required")
        if not all([origin, destination, month]):
            raise ValueError("Origin, destination, and month are required parameters")

        # Build query parameters
        params = {
            "show_to_affiliates": str(show_to_affiliates).lower(),
            "currency": self.currency,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "month": month,
            "token": self.token,
        }

        try:
            # Make the request
            with httpx.Client(timeout=self.api_request_timeout) as client:
                response = client.get(
                    f"{self.base_url_v2}/v2/prices/month-matrix", params=params
                )
                response.raise_for_status()
                response = response.json()
                response["data"] = [
                    sorted(response["data"], key=lambda x: x["depart_date"])
                ]
                return response
        except Exception:
            return None

    def get_prices_for_dates(
        self,
        origin: str,
        destination: str,
        departure_at: str,
        return_at: Optional[str] = None,
        unique: bool = False,
        sorting: str = "price",
        direct: bool = False,
        limit: int = 30,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Get flight prices for specific dates from Aviasales v3 API.

        Args:
            origin: Origin airport IATA code (e.g., "MAD")
            destination: Destination airport IATA code (e.g., "BCN")
            departure_at: Departure date in YYYY-MM format (e.g., "2023-07")
            return_at: Return date in YYYY-MM format (optional, e.g., "2023-08")
            unique: Show unique carriers only (default: False)
            sorting: Sorting option: "price", "route", or "date" (default: "price")
            direct: Show only direct flights (default: False)
            limit: Number of results per page (default: 30, max: 1000)
            page: Page number (default: 1)
            one_way: One-way flight search (default: True)

        Returns:
            Dictionary containing API response with flight data

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If required parameters are missing or invalid
        """
        # Validate required parameters
        if not self.token:
            raise ValueError("API token is required")
        if not all([origin, destination, departure_at]):
            raise ValueError("Origin, destination, and departure_at are required")

        # Validate sorting parameter
        valid_sorting = ["price", "route"]
        if sorting not in valid_sorting:
            raise ValueError(f"sorting must be one of: {', '.join(valid_sorting)}")

        # Build query parameters
        params = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_at": departure_at,
            "unique": str(unique).lower(),
            "sorting": sorting,
            "direct": direct,
            "cy": self.currency,
            "limit": limit,
            "page": page,
            # "one_way": str(one_way).lower(),
            "token": self.token,
        }

        # Add optional return_at parameter if provided
        if return_at:
            params["return_at"] = return_at

        # Make the request
        with httpx.Client(timeout=self.api_request_timeout) as client:
            response = client.get(
                f"{self.base_url_v3}/prices_for_dates",
                params=params,
            )
            response.raise_for_status()
            return response.json()


if __name__ == "__main__":
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.getcwd(), ".env")

    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    client = TravelPayoutsClient(
        token=os.getenv("TRAVEL_PAYOUTS_TOKEN"),  # type: ignore
    )
    origin = "MOW"
    destination = "LED"
    month = "2026-03-01"

    result = client.get_monthly_prices(
        origin=origin,
        destination=destination,
        month=month,
    )
    with open("month_prices.json", "w") as file:
        json.dump(result, file)

    client = TravelPayoutsClient(
        token=os.getenv("TRAVEL_PAYOUTS_TOKEN"),  # type: ignore
    )
    departure_at = "2026-04-03"
    print(
        client.get_prices_for_dates(
            origin=origin, destination=destination, departure_at=departure_at, limit=50
        )
    )
