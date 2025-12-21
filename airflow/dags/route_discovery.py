# dags/route_discovery_dag.py
from datetime import datetime, timedelta
from typing import List
from airflow import DAG
from airflow.sdk import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.python import PythonOperator

from db.models.request import Request
from db.dependencies import get_request_dao

# from func.trip_inverval import generate_trip_intervals

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

# INSERT INTO users VALUES (1, 234324, 'alex_zdrn', 'alex', 'zdrn');

# INSERT INTO users (id, telegram_id, username, first_name, last_name)
# VALUES
#     (1, 123456789, 'john_doe', 'John', 'Doe'),
#     (2, 987654321, 'jane_smith', 'Jane', 'Smith'),
#     (3, 555555555, 'alex_jones', 'Alex', 'Jones'),
#     (4, 777777777, 'sara_miller', 'Sara', 'Miller'),
#     (5, 888888888, 'mike_brown', 'Mike', 'Brown')
# ON CONFLICT (id) DO NOTHING;

# -- Insert mock requests
# INSERT INTO requests (user_id, departure, arrival, adults, round_trip, created_at, status)
# VALUES
#     -- User 1 requests
#     (1, 'LHR', 'JFK', 2, TRUE, '2024-01-15 10:30:00', 'init'),
#     (1, 'CDG', 'LAX', 1, FALSE, '2024-01-16 14:45:00', 'init'),
#     (1, 'AMS', 'SFO', 3, TRUE, '2024-01-17 09:15:00', 'processed'),

#     -- User 2 requests
#     (2, 'JFK', 'LHR', 2, TRUE, '2024-01-18 11:20:00', 'init'),
#     (2, 'LAX', 'CDG', 1, FALSE, '2024-01-19 16:30:00', 'failed'),
#     (2, 'SFO', 'AMS', 4, TRUE, '2024-01-20 08:45:00', 'init')
# ON CONFLICT (id) DO NOTHING;

with DAG(
    "route_discovery_dag_v12",
    default_args=default_args,
    schedule="0 */3 * * *",
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
        ti = context["ti"]
        requests: List[Request] = ti.xcom_pull(task_ids="fetch_init_requests")

        # Process requests and generate intervals
        all_routes = {}
        for request in requests:
            print(f"Processing request: {request=}")
            # Your logic to generate intervals
            pass
            # intervals = generate_trip_intervals(
            #     # ... parameters based on request ...
            # )
            all_routes[request.id] = 1

        return all_routes

    expand_routes_task = PythonOperator(
        task_id="expand_routes",
        python_callable=process_and_expand_routes,
    )

    # Task 3: Save routes to database
    def prepare_save_query(**context):
        ti = context["ti"]
        routes_data = ti.xcom_pull(task_ids="expand_routes")

        # Build dynamic SQL based on routes_data
        # ... your query building logic ...

        return "SELECT 1;"  # Placeholder SQL

    prepare_query = PythonOperator(
        task_id="prepare_save_query",
        python_callable=prepare_save_query,
    )

    save_routes = SQLExecuteQueryOperator(
        task_id="save_routes",
        conn_id="pg_tickets",
        sql="{{ ti.xcom_pull(task_ids='prepare_save_query') }}",
    )

    # Set task dependencies
    fetch_init_requests_task >> expand_routes_task >> prepare_query >> save_routes
