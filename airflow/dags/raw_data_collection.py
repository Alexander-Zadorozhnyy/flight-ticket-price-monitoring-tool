# dags/route_discovery_dag.py
from datetime import datetime, timedelta
import sys
from typing import List, Tuple
from airflow import DAG
from airflow.sdk import dag, task
from airflow.providers.standard.operators.python import PythonOperator

from scrapers.kypibilit_scraper import scrape_flights
from db.models.request import Request
from db.dependencies import get_request_dao, get_route_dao

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

with DAG(
    "raw_data_collection_dag_v9",
    default_args=default_args,
    schedule="0 */2 * * *",
    catchup=False,
    tags=["routes"],
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
        print(f"{requests_data=}")
        for request_id, adults in requests_data:
            print(f"{request_id=} {adults=}")
            for r in dao.get_by_request_id(request_id):
                print(f"{r=}")
                routes = [r.to_dict() | {"adults": adults} ]
            routes.extend(routes)
            
        print(f"Fetched routes to collect size: {sys.getsizeof(routes)}")
        return routes

    # Task 2: Fetch existing routes for all requests to collect data (Python function)
    fetch_routes_to_collect_task = PythonOperator(
        task_id="fetch_routes_to_collect",
        python_callable=fetch_routes_to_collect,
    )

    def collect_raw_data_by_kypibilet(**context):
        ti = context["ti"]
        routes_data: List[dict] = ti.xcom_pull(
            task_ids="fetch_routes_to_collect"
        )

        # Here is the logic to collect raw data using kypibilet
        for route in routes_data:
            print(f"Collecting data for route: {route}")
            flights = scrape_flights(
                origin=route["departure"],
                destination=route["arrival"],
                departure_date=datetime.fromisoformat(route["departure_date"]),
                adults=route["adults"],
            )
            print(f"Collected flights: {flights}, {route=}")

        return True
    
    # Task 3: Collect raw data using kypibilet (Python function)
    collect_raw_data_by_kypibilet_task = PythonOperator(
        task_id="collect_raw_data_by_kypibilet",
        python_callable=collect_raw_data_by_kypibilet,
    )

    # # Task 2: Expand routes (Python function)
    # def process_and_expand_routes(**context):
    #     def get_options(options_dict, key, default):
    #         if options_dict and key in options_dict:
    #             return options_dict[key]
    #         return default

    #     ti = context["ti"]
    #     requests: List[dict] = ti.xcom_pull(task_ids="fetch_init_requests")

    #     # Process requests and generate intervals
    #     all_routes = {}
    #     for request in requests:
    #         print(
    #             f"Processing request: {request=}, {type(request["departure_start_period"])=}, {type(request["departure_end_period"])=}"
    #         )

    #         intervals = generate_trip_intervals(
    #             start_date=datetime.fromisoformat(request["departure_start_period"]),
    #             end_date=datetime.fromisoformat(request["departure_end_period"]),
    #             departure_days=get_options(
    #                 request.get("departure_options", {}), "preferred_days", None
    #             ),
    #             return_days=get_options(
    #                 request.get("arrival_options", {}), "preferred_days", None
    #             ),
    #             desired_duration=request["duration"],
    #             duration_variance=2,
    #             max_intervals=100,
    #         )
    #         all_routes[request["id"]] = {
    #             "intervals": intervals,
    #             "departure": request["departure"],
    #             "arrival": request["arrival"],
    #             "round_trip": request["round_trip"],
    #         }

    #     return all_routes

    # expand_routes_task = PythonOperator(
    #     task_id="expand_routes",
    #     python_callable=process_and_expand_routes,
    # )

    # # Task 3: Save routes to database
    # def create_routes(**context):
    #     dao = get_route_dao()

    #     ti = context["ti"]
    #     routes = ti.xcom_pull(task_ids="expand_routes")
    #     for request_id, interval_data in routes.items():
    #         for interval in interval_data["intervals"]:
    #             dao.create(
    #                 {
    #                     "request_id": request_id,
    #                     "departure": interval_data["departure"],
    #                     "arrival": interval_data["arrival"],
    #                     "departure_date": interval["departure_date"],
    #                     "route_type": "to_destination",
    #                 }
    #             )
    #             if interval_data["round_trip"]:
    #                 dao.create(
    #                     {
    #                         "request_id": request_id,
    #                         "departure": interval_data["arrival"],
    #                         "arrival": interval_data["departure"],
    #                         "departure_date": interval["return_date"],
    #                         "route_type": "return",
    #                     }
    #                 )

    #     return list(routes.keys())

    # create_routes_task = PythonOperator(
    #     task_id="create_routes",
    #     python_callable=create_routes,
    # )

    # # Task 4: Mark requests as processed
    # def mark_requests_processed(**context):
    #     dao = get_request_dao()

    #     ti = context["ti"]
    #     proceed_request_ids = ti.xcom_pull(task_ids="create_routes")

    #     dao.update_status_bulk(proceed_request_ids, new_status="data_collecting")

    # mark_requests_processed_task = PythonOperator(
    #     task_id="mark_requests_processed",
    #     python_callable=mark_requests_processed,
    # )

    # Set task dependencies
    fetch_data_collection_requests_task >> fetch_routes_to_collect_task >> collect_raw_data_by_kypibilet_task
