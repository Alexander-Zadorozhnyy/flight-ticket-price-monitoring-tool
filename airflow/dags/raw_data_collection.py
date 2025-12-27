# dags/raw_data_collection.py
from datetime import datetime, timedelta
from typing import List, Tuple
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from minio_utils.buckets import Bucket
from scrapers.kypibilit_scraper import scrape_flights as kypibilet_scrape_fligths
from scrapers.tripcom_scraper import scrape_flights as tripcom_scrape_fligths
from db.models.request import Request
from db.dependencies import (
    get_minio_client,
    get_request_dao,
    get_route_dao,
    get_session_dao,
)

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

with DAG(
    "raw_data_collection_dag_v17",
    default_args=default_args,
    schedule="0 */3 * * *",
    catchup=False,
    tags=["routes", "data_collection"],
) as dag:

    def fetch_data_collection_requests(**context):
        dao = get_request_dao()
        requests: List[Request] = dao.get_all(status="data_collecting")

        return [(r.id, r.adults) for r in requests]

    # Task 1: Fetch data collection requests (Python function)
    fetch_data_collection_requests_task = PythonOperator(
        task_id="fetch_data_collection_requests",
        python_callable=fetch_data_collection_requests,
    )

    def fetch_routes_to_collect(**context):
        ti = context["ti"]
        requests_data: List[Tuple[int, int]] = ti.xcom_pull(
            task_ids="fetch_data_collection_requests"
        )

        dao = get_route_dao()

        routes = []
        # print(f"{requests_data=}")
        for request_id, adults in requests_data:
            for r in dao.get_by_request_id(request_id):
                routes.append(r.to_dict() | {"adults": adults})

        # print(f"Fetched routes to collect size: {sys.getsizeof(routes)}")
        return routes

    # Task 2: Fetch existing routes for all requests to collect data (Python function)
    fetch_routes_to_collect_task = PythonOperator(
        task_id="fetch_routes_to_collect",
        python_callable=fetch_routes_to_collect,
    )

    def collect_raw_data_by_kypibilet(**context):
        ti = context["ti"]
        routes_data: List[dict] = ti.xcom_pull(task_ids="fetch_routes_to_collect")

        minio_client = get_minio_client()
        minio_client.create_bucket(Bucket.Kypibilet.value)
        session_time = datetime.now().isoformat(timespec="seconds")

        # Here is the logic to collect raw data using kypibilet
        for route in routes_data:
            try:
                # print(f"Collecting data for route: {route}")
                flights = kypibilet_scrape_fligths(
                    origin=route["departure"],
                    destination=route["arrival"],
                    departure_date=datetime.fromisoformat(route["departure_date"]),
                    adults=route["adults"],
                )

                print(f"Collected flights: {flights}, {route=}")

                minio_client.upload_dict(
                    Bucket.Kypibilet.value,
                    {"flights": flights, "session_time": session_time},
                    f"route_{route['id']}_{session_time}.json",
                )
            except Exception as e:
                print(f"Error while collection route fligths: {e}")
                continue

        return session_time

    # Task 3: Collect raw data using kypibilet (Python function)
    collect_raw_data_by_kypibilet_task = PythonOperator(
        task_id="collect_raw_data_by_kypibilet",
        python_callable=collect_raw_data_by_kypibilet,
    )

    def collect_raw_data_by_tripcom(**context):
        ti = context["ti"]
        routes_data: List[dict] = ti.xcom_pull(task_ids="fetch_routes_to_collect")

        minio_client = get_minio_client()
        minio_client.create_bucket(Bucket.Tripcom.value)
        session_time = datetime.now().isoformat(timespec="seconds")

        # Here is the logic to collect raw data using kypibilet
        for route in routes_data:
            try:
                # print(f"Collecting data for route: {route}")
                flights = tripcom_scrape_fligths(
                    origin=route["departure"],
                    destination=route["arrival"],
                    departure_date=datetime.fromisoformat(route["departure_date"]),
                    adults=route["adults"],
                )

                print(f"Collected flights: {flights}, {route=}")

                minio_client.upload_dict(
                    Bucket.Tripcom.value,
                    {"flights": flights, "session_time": session_time},
                    f"route_{route['id']}_{session_time}.json",
                )
            except Exception as e:
                print(f"Error while collection route fligths: {e}")
                continue

        return session_time

    # Task 4: Collect raw data using tripcom (Python function)
    collect_raw_data_by_tripcom_task = PythonOperator(
        task_id="collect_raw_data_by_tripcom",
        python_callable=collect_raw_data_by_tripcom,
    )

    def save_sessions(**context):
        ti = context["ti"]
        dao = get_session_dao()

        session_time: datetime = datetime.fromisoformat(
            ti.xcom_pull(task_ids="collect_raw_data_by_kypibilet")
        )
        dao.create(
            obj_data={
                "search_at": session_time,
                "site_aggregator": Bucket.Kypibilet.name,
                "status": "init",
            }
        )

        session_time: datetime = datetime.fromisoformat(
            ti.xcom_pull(task_ids="collect_raw_data_by_tripcom")
        )
        dao.create(
            obj_data={
                "search_at": session_time,
                "site_aggregator": Bucket.Tripcom.name,
                "status": "init",
            }
        )

    # Task 5: Save session data for future ETL
    save_sessions_task = PythonOperator(
        task_id="save_sessions",
        python_callable=save_sessions,
    )

    # Set task dependencies
    (
        fetch_data_collection_requests_task
        >> fetch_routes_to_collect_task
        >> collect_raw_data_by_kypibilet_task
        >> collect_raw_data_by_tripcom_task
        >> save_sessions_task
    )
