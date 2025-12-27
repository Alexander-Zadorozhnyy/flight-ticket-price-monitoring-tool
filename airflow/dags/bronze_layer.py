# dags/bronze_layer.py
from datetime import timedelta
from typing import Dict, List

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from minio_utils.buckets import Bucket
from db.models import SearchSession
from db.dependencies import get_minio_client, get_request_dao, get_session_dao

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

with DAG(
    "bronze_layer_processing_v1",
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
        minio_client = get_minio_client()
        
        sessions: Dict[str, List[dict]] = ti.xcom_pull(task_ids="fetch_init_sessions") # 
        need_sessions: List[dict] = sessions.get(Bucket.Kypibilet.name, [])
        
        if not need_sessions:
            print("No data to transform!")
            return None
        
        result = []
        
        for s in need_sessions:
            session_time = s.get("search_at", None)
            
            if session_time is None:
                continue
            
            files = minio_client.get_files_by_time(Bucket.Kypibilet.value, session_time)

    transform_kypibilet_task = PythonOperator(
        task_id="transform_kypibilet",
        python_callable=transform_kypibilet_sessions,
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
