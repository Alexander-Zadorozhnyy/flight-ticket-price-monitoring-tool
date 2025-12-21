from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}


def greet(ti):
    first_name = ti.xcom_pull(task_ids="get_name", key="first_name")
    second_name = ti.xcom_pull(task_ids="get_name", key="second_name")
    age = ti.xcom_pull(task_ids="get_age", key="age")
    print(f"Hello, {first_name} {second_name}, {age} y.o.!")


def get_name(ti):
    ti.xcom_push(key="first_name", value="Jerry")
    ti.xcom_push(key="second_name", value="Friedman")


def get_age(ti):
    ti.xcom_push(key="age", value=22)


with DAG(
    dag_id="dag_python_example_v4",
    default_args=default_args,
    description="This is first pyhton dag we write!",
    start_date=datetime(2025, 5, 12, 14, 00),
    schedule="* * * * *",
) as dag:
    task1 = PythonOperator(
        task_id="greet", python_callable=greet, op_kwargs={"name": "Alex", "age": 20}
    )

    task2 = PythonOperator(task_id="get_name", python_callable=get_name)
    task3 = PythonOperator(task_id="get_age", python_callable=get_age)

    [task2, task3] >> task1

    # Straightforward
    # task1.set_downstream(task2)
    # task1.set_downstream(task3)

    # Operator using
    # task1 >> task2
    # task1 >> task3

    # Updagraded operator using
    # task1 >> [task2, task3]
