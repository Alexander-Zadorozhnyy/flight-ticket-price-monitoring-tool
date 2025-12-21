from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

default_args = {"owner": "alex_zdrn", "retries": 5, "retry_delay": timedelta(minutes=5)}


with DAG(
    dag_id="dag_with_postgres_operator_v08",
    default_args=default_args,
    start_date=datetime(2025, 12, 5),
    schedule="0 0 * * *",
) as dag:
    task1 = SQLExecuteQueryOperator(
        task_id="create_postgres_table",
        conn_id="postgres_localhost",
        sql="""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT FROM pg_tables 
                WHERE  schemaname = 'public' 
                AND    tablename  = 'dag_runs'
            ) THEN
                CREATE TABLE dag_runs (
                    dt date,
                    dag_id character varying,
                    PRIMARY KEY (dt, dag_id)
                );
            END IF;
        END $$;
        """,
    )

    task2 = SQLExecuteQueryOperator(
        task_id="insert_into_table",
        conn_id="postgres_localhost",
        sql="""
            INSERT INTO dag_runs (dt, dag_id) VALUES ('{{ ds }}', '{{ dag.dag_id }}')
            ON CONFLICT (dt, dag_id) 
            DO NOTHING;
        """,
    )

    task3 = SQLExecuteQueryOperator(
        task_id="delete_data_from_table",
        conn_id="postgres_localhost",
        sql="""
            delete from dag_runs where dt = '{{ ds }}' and dag_id = '{{ dag.dag_id }}';
        """,
    )
    task1 >> task3 >> task2
