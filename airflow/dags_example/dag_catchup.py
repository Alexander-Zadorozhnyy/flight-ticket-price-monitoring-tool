from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=1)}

with DAG(
    dag_id="dag_catchup_example_v1",
    default_args=default_args,
    description="This is first catchup dag we write!",
    start_date=datetime(2025, 12, 1, 13, 35),
    schedule="@daily", # https://crontab.guru
    catchup=True,
) as dag:
    task1 = BashOperator(task_id="first", bash_command="echo hello_world")
    
    task1