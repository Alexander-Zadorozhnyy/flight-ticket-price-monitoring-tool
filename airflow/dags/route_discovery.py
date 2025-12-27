# dags/route_discovery_dag.py
from datetime import datetime, timedelta
from typing import List
from airflow import DAG
from airflow.sdk import dag, task
from airflow.providers.standard.operators.python import PythonOperator

from db.models.request import Request
from db.dependencies import get_request_dao, get_route_dao

from func.trip_inverval import generate_trip_intervals

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

with DAG(
    "route_discovery_dag_v2",
    default_args=default_args,
    schedule="*/5 * * * *",
    catchup=False,
    tags=["routes"],
) as dag:

    def fetch_init_requests(**context):
        dao = get_request_dao()
        requests: List[Request] = dao.get_all(status="init")

        return [r.to_dict() for r in requests]

    fetch_init_requests_task = PythonOperator(
        task_id="fetch_init_requests",
        python_callable=fetch_init_requests,
    )

    # Task 2: Expand routes (Python function)
    def process_and_expand_routes(**context):
        def get_options(options_dict, key, default):
            if options_dict and key in options_dict:
                return options_dict[key]
            return default

        ti = context["ti"]
        requests: List[dict] = ti.xcom_pull(task_ids="fetch_init_requests")

        # Process requests and generate intervals
        all_routes = {}
        for request in requests:
            print(
                f"Processing request: {request=}, {type(request["departure_start_period"])=}, {type(request["return_end_period"])=}"
            )

            intervals = generate_trip_intervals(
                start_date=datetime.fromisoformat(request["departure_start_period"]),
                end_date=datetime.fromisoformat(request["return_end_period"]),
                departure_days=get_options(
                    request.get("departure_options", {}), "preferred_days", None
                ),
                return_days=get_options(
                    request.get("arrival_options", {}), "preferred_days", None
                ),
                desired_duration=request["duration"],
                duration_variance=2,
                max_intervals=100,
            )
            all_routes[request["id"]] = {
                "intervals": intervals,
                "departure": request["departure"],
                "arrival": request["arrival"],
                "round_trip": request["round_trip"],
            }

        return all_routes

    expand_routes_task = PythonOperator(
        task_id="expand_routes",
        python_callable=process_and_expand_routes,
    )

    # Task 3: Save routes to database
    def create_routes(**context):
        dao = get_route_dao()

        ti = context["ti"]
        departure_added, arrival_added = set(), set()
        routes = ti.xcom_pull(task_ids="expand_routes")
        for request_id, interval_data in routes.items():
            for interval in interval_data["intervals"]:
                if interval["departure_date"] not in departure_added:
                    dao.create(
                        {
                            "request_id": request_id,
                            "departure": interval_data["departure"],
                            "arrival": interval_data["arrival"],
                            "departure_date": interval["departure_date"],
                            "route_type": "to_destination",
                        }
                    )
                    departure_added.add(interval["departure_date"])
                if (
                    interval_data["round_trip"]
                    and interval["return_date"] not in arrival_added
                ):
                    dao.create(
                        {
                            "request_id": request_id,
                            "departure": interval_data["arrival"],
                            "arrival": interval_data["departure"],
                            "departure_date": interval["return_date"],
                            "route_type": "return",
                        }
                    )
                    arrival_added.add(interval["return_date"])

        return list(routes.keys())

    create_routes_task = PythonOperator(
        task_id="create_routes",
        python_callable=create_routes,
    )

    # Task 4: Mark requests as processed
    def mark_requests_processed(**context):
        dao = get_request_dao()

        ti = context["ti"]
        proceed_request_ids = ti.xcom_pull(task_ids="create_routes")

        dao.update_status_bulk(proceed_request_ids, new_status="data_collecting")

    mark_requests_processed_task = PythonOperator(
        task_id="mark_requests_processed",
        python_callable=mark_requests_processed,
    )

    # Set task dependencies
    (
        fetch_init_requests_task
        >> expand_routes_task
        >> create_routes_task
        >> mark_requests_processed_task
    )
