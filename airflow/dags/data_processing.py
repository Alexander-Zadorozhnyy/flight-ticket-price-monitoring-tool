# dags/bronze_layer.py
from datetime import timedelta
from typing import Dict, List

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from bronze_layer.structure_data_tripcom import TripcomDataTransformer
from bronze_layer.bronze_data_processor import BronzeDataProcessor
from bronze_layer.structure_data_kypibilet import KypibiletDataTransformer
from aggregation_layers.view_manager import ViewManager
from minio_utils.buckets import Bucket

from db.models import SearchSession
from db.dependencies import (
    get_flight_dao,
    get_flight_price_dao,
    get_minio_client,
    get_route_dao,
    get_session_dao,
    get_simple_db,
)

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}

with DAG(
    "data_processing_v8",
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

    # Task 2.1: Transform all flights from Kypibilet (Python function)
    def bronze_layer_transform_kypibilet_sessions(**context):
        ti = context["ti"]

        sessions: Dict[str, List[dict]] = ti.xcom_pull(task_ids="fetch_init_sessions")
        need_sessions: List[dict] = sessions.get(Bucket.Kypibilet.name, [])

        if not need_sessions:
            print("No data to transform!")
            return None

        route_dao = get_route_dao()
        flight_dao = get_flight_dao()
        flight_price_dao = get_flight_price_dao()
        session_dao = get_session_dao()

        minio_client = get_minio_client()

        processor = BronzeDataProcessor(
            transformer=KypibiletDataTransformer(),
            minio_client=minio_client,
            route_dao=route_dao,
            flight_dao=flight_dao,
            flight_price_dao=flight_price_dao,
        )

        processed_sessions = processor.process_sessions(
            sessions=need_sessions, bucket_name=Bucket.Kypibilet.value
        )

        for s in processed_sessions:
            session_dao.update(
                session_dao.get(s[0]), {"status": "proceed", "quality": s[1]}
            )

    bronze_layer_transform_kypibilet_task = PythonOperator(
        task_id="bronze_layer_transform_kypibilet",
        python_callable=bronze_layer_transform_kypibilet_sessions,
    )

    # Task 2.2: Transform all flights from Tripcom (Python function)
    def bronze_layer_transform_tripcom_sessions(**context):
        ti = context["ti"]

        sessions: Dict[str, List[dict]] = ti.xcom_pull(task_ids="fetch_init_sessions")
        need_sessions: List[dict] = sessions.get(Bucket.Tripcom.name, [])

        if not need_sessions:
            print("No data to transform!")
            return None

        route_dao = get_route_dao()
        flight_dao = get_flight_dao()
        flight_price_dao = get_flight_price_dao()
        session_dao = get_session_dao()

        minio_client = get_minio_client()

        processor = BronzeDataProcessor(
            transformer=TripcomDataTransformer(
                airline_codes_file="/opt/airflow/bronze_layer/utils/airline_codes_simple.json",
            ),
            minio_client=minio_client,
            route_dao=route_dao,
            flight_dao=flight_dao,
            flight_price_dao=flight_price_dao,
        )
        try:
            processed_sessions = processor.process_sessions(
                sessions=need_sessions, bucket_name=Bucket.Tripcom.value
            )
        except Exception:
            import traceback

            traceback.print_exc()
            return

        for s in processed_sessions:
            session_dao.update(
                session_dao.get(s[0]), {"status": "proceed", "quality": s[1]}
            )

    bronze_layer_transform_tripcom_task = PythonOperator(
        task_id="bronze_layer_transform_tripcom",
        python_callable=bronze_layer_transform_tripcom_sessions,
    )

    def silver_layer_processing(**context):
        view_manager = ViewManager(
            db=get_simple_db(),
            views_folder="/opt/airflow/aggregation_layers/silver_views",
        )
        view_manager.create_views()
        view_manager.resresh_views()

    silver_layer_processing_task = PythonOperator(
        task_id="silver_layer_processing",
        python_callable=silver_layer_processing,
    )

    def golden_layer_processing(**context):
        view_manager = ViewManager(
            db=get_simple_db(),
            views_folder="/opt/airflow/aggregation_layers/golden_views",
        )
        view_manager.create_views()
        view_manager.resresh_views()

    golden_layer_processing_task = PythonOperator(
        task_id="golden_layer_processing",
        python_callable=golden_layer_processing,
    )

    # Set task dependencies
    fetch_init_sessions_task >> [bronze_layer_transform_kypibilet_task, bronze_layer_transform_tripcom_task] >> silver_layer_processing_task >> golden_layer_processing_task
