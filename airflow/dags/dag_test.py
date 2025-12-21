from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime

with DAG(
    "test_connection_v3",
    start_date=datetime.now(),
    catchup=False,
) as dag:
    test_task = SQLExecuteQueryOperator(
        task_id="test_postgres_connection",
        conn_id="postgres",  # Try this first
        sql="SELECT 1;",
    )
