from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}


with DAG(
    dag_id="dag_bash_example_v5",
    default_args=default_args,
    description="This is first dag we write!",
    start_date=datetime(2025, 5, 12, 13, 35),
    schedule="@daily",
) as dag:
    task1 = BashOperator(task_id="first", bash_command="echo hello_world")
    task2 = BashOperator(task_id="second", bash_command="echo hey, am the second task!")
    task3 = BashOperator(task_id="third", bash_command="echo hey, am the third task that runs after firts parallel with task2!")
    
    # Straightforward
    # task1.set_downstream(task2)
    # task1.set_downstream(task3)
     
    # Operator using
    # task1 >> task2
    # task1 >> task3
    
    # Updagraded operator using
    task1 >> [task2, task3]
    
    
    
