from datetime import datetime
from typing import List, Optional, Tuple, Union


from db.dao.flight_price import FlightPriceDAO
from db.models.flight import Flight
from db.dao.flight import FlightDAO
from db.dao.route import RouteDAO
from minio_utils.minio_client import MinIOClient
from transformers.structure_data_tripcom import TripcomDataTransformer
from transformers.structure_data_kypibilet import KypibiletDataTransformer
from transformers.quality import Quality, QualityCalculator


class BronzeDataProcessor:
    def __init__(
        self,
        transformer: Union[KypibiletDataTransformer, TripcomDataTransformer],
        minio_client: MinIOClient,
        route_dao: RouteDAO,
        flight_dao: FlightDAO,
        flight_price_dao: FlightPriceDAO,
    ):
        self.transformer = transformer
        self.minio_client = minio_client

        self.route_dao = route_dao
        self.flight_dao = flight_dao
        self.flight_price_dao = flight_price_dao

        self.quality_calculator = QualityCalculator()

    def process_sessions(
        self, sessions: List[dict], bucket_name: str
    ) -> List[Tuple[int, dict]]:
        processed_sessions = []

        for s in sessions:
            session_time = s.get("search_at", None)
            transformed_data = {}

            if session_time is None:
                continue

            transformed_data = self.get_transformed_data(bucket_name, session_time)
            qualities = []

            for route_id, flights_data in transformed_data.items():
                flights, quality = flights_data
                qualities.append(quality)

                print(f"{route_id=}, {quality=}")

                for flight_data in flights:
                    try:
                        flight = self.get_flight(route_id, flight_data)

                        if flight is None:
                            continue

                        self.flight_price_dao.create(
                            obj_data=dict(
                                flight_id=flight.id,
                                search_session_id=s["id"],
                                found_at=datetime.fromisoformat(session_time),
                                amount=flight_data["price"]["amount"],
                                currency=flight_data["price"]["currency"],
                                cashback_amount=flight_data["price"].get(
                                    "cashback_amount"
                                ),
                                cashback_currency=flight_data["price"].get(
                                    "cashback_currency"
                                ),
                            )
                        )
                    except Exception as e:
                        print(f"Error creating flight price objects: {str(e)}")

            processed_sessions.append(
                [s["id"], self.quality_calculator.merge_batch_qualities(qualities)]
            )
        return processed_sessions

    def get_transformed_data(self, bucket_name, session_time):
        transformed_data = {}
        route_flights = self.minio_client.get_files_by_time(bucket_name, session_time)

        for filename, flights in route_flights.items():
            route_id = int(filename.split("_")[1])
            route = self.route_dao.get(route_id)

            if route is None:
                continue

            data, quality = self.transformer.structure_flight_output_list(
                flights.get("flights", []), route.departure_date
            )

            if data and quality.overall_quality != Quality.VERY_POOR:
                transformed_data[route_id] = [data, quality]

        return transformed_data

    def get_flight(self, route_id: int, flight_data: dict) -> Optional[Flight]:
        try:
            flight = self.flight_dao.find_by_params(
                route_id=route_id,
                departure_at=datetime.fromisoformat(
                    flight_data["departure"]["datetime"]
                ),
                arrival_at=datetime.fromisoformat(flight_data["arrival"]["datetime"]),
                airline_code=flight_data["airline"],
            )

            if flight:
                return flight

            flight_obj = self.flight_dao.create(
                obj_data=dict(
                    route_id=route_id,
                    airline_code=flight_data["airline"],
                    departure_at=datetime.fromisoformat(
                        flight_data["departure"]["datetime"]
                    ),
                    arrival_at=datetime.fromisoformat(
                        flight_data["arrival"]["datetime"]
                    ),
                    duration=flight_data["duration"]["total_minutes"],
                    is_direct=flight_data["stops"]["is_direct"],
                    stop_count=flight_data["stops"]["count"],
                    baggage_included=flight_data["services"]["baggage"],
                    baggage_type=flight_data["services"]["baggage_type"],
                    seats_left=flight_data["services"]["seats_left"],
                )
            )
            return flight_obj
        except Exception as e:
            print(f"Error getting flight object: {str(e)}")
            return None
