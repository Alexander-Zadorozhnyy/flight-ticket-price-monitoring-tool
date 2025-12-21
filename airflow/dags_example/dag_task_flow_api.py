from datetime import datetime, timedelta

from airflow.sdk import dag, task

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}


@dag(
    dag_id="dag_taskflow_v2",
    default_args=default_args,
    description="This is first pyhton dag we write!",
    start_date=datetime(2025, 5, 12, 14, 00),
    schedule="* * * * *",
)
def hello_world_etl():
    @task(multiple_outputs=True)
    def get_name():
        return {"first_name": "Jerry", "second_name": "FF"}

    @task()
    def get_age():
        return 19

    @task()
    def greet(first_name, second_name, age):
        print(f"Hello, {first_name} {second_name}. Your age is {age}!")

    name_dict = get_name()
    age = get_age()
    greet(
        first_name=name_dict["first_name"],
        second_name=name_dict["second_name"],
        age=age,
    )


greet_dag = hello_world_etl()
