# dags/bronze_layer.py
from datetime import datetime, timedelta
from typing import Dict, List

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from transformers.structure_data_kypibilet import KypibiletDataTransformer
from minio_utils.buckets import Bucket
from db.models import SearchSession
from db.dependencies import (
    get_flight_dao,
    get_flight_price_dao,
    get_minio_client,
    get_route_dao,
    get_session_dao,
)

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

with DAG(
    "bronze_layer_processing_v8",
    default_args=default_args,
    schedule="*/5 * * * *",
    catchup=False,
    tags=["data_collection", "data_processing"],
) as dag:

    def fetch_init_sessions():
        dao = get_session_dao()
        sessions: Dict[str, List[SearchSession]] = dao.get_grouped_sessions(
            status="init"
        )

        for k, v in sessions.items():
            sessions[k] = [s.to_dict() for s in v]

        return sessions

    fetch_init_sessions_task = PythonOperator(
        task_id="fetch_init_sessions",
        python_callable=fetch_init_sessions,
    )

    # Task 2: Transform all flights from (Python function)
    def transform_kypibilet_sessions(**context):
        ti = context["ti"]
        route_dao = get_route_dao()
        flight_dao = get_flight_dao()
        flight_price_dao = get_flight_price_dao()
        session_dao = get_session_dao()

        minio_client = get_minio_client()

        transformer = KypibiletDataTransformer()

        sessions: Dict[str, List[dict]] = ti.xcom_pull(
            task_ids="fetch_init_sessions"
        )  #
        need_sessions: List[dict] = sessions.get(Bucket.Kypibilet.name, [])

        if not need_sessions:
            print("No data to transform!")
            return None

        for s in need_sessions:
            session_time = s.get("search_at", None)
            transformed_data = {}

            if session_time is None:
                continue

            route_flights = minio_client.get_files_by_time(
                Bucket.Kypibilet.value, session_time
            )

            for filename, flights in route_flights.items():
                route_id = int(filename.split("_")[1])
                route = route_dao.get(route_id)

                if route is None:
                    continue

                data = transformer.structure_flight_output_list(
                    flights.get("flights", []), route.departure_date
                )

                if data:
                    transformed_data[route_id] = data

            for route_id, flights in transformed_data.items():
                for flight in flights:
                    try:
                        flight_obj = flight_dao.find_by_params(
                            route_id=route_id,
                            departure_at=datetime.fromisoformat(
                                flight["departure"]["datetime"]
                            ),
                            arrival_at=datetime.fromisoformat(
                                flight["arrival"]["datetime"]
                            ),
                            airline_code=flight["airline"],
                        )

                        if not flight_obj:
                            flight_obj = flight_dao.create(
                                obj_data=dict(
                                    route_id=route_id,
                                    airline_code=flight["airline"],
                                    departure_at=datetime.fromisoformat(
                                        flight["departure"]["datetime"]
                                    ),
                                    arrival_at=datetime.fromisoformat(
                                        flight["arrival"]["datetime"]
                                    ),
                                    duration=flight["duration"]["total_minutes"],
                                    is_direct=flight["stops"]["is_direct"],
                                    stop_count=flight["stops"]["count"],
                                    baggage_included=flight["services"]["baggage"],
                                    baggage_type=flight["services"]["baggage_type"],
                                    seats_left=flight["services"]["seats_left"],
                                )
                            )
                        flight_price_dao.create(
                            obj_data=dict(
                                flight_id=flight_obj.id,
                                search_session_id=s["id"],
                                found_at=datetime.fromisoformat(session_time),
                                amount=flight["price"]["amount"],
                                currency=flight["price"]["currency"],
                                cashback_amount=flight["price"].get("cashback_amount"),
                                cashback_currency=flight["price"].get(
                                    "cashback_currency"
                                ),
                            )
                        )
                    except Exception as e:
                        print(f"Error while creating db objects: {str(e)}")

            session_dao.update(session_dao.get(s["id"]), {"status": "proceed"})

    transform_kypibilet_task = PythonOperator(
        task_id="transform_kypibilet",
        python_callable=transform_kypibilet_sessions,
    )

    # Set task dependencies
    fetch_init_sessions_task >> transform_kypibilet_task
