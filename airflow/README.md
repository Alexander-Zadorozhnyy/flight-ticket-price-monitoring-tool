# Installation Guide

Detailed documentation: <https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html>

## Have to go steps

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.1.3/docker-compose.yaml'
```

Change airlflow executor to LocalExecutor and remove Redis with Celery

for linux

```bash
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

If you want to initialize airflow.cfg with default values before launching the airflow service, run.

```bash
docker compose run airflow-cli airflow config list
docker compose up airflow-init
```

After initialization is complete, you should see output related to files, folders, and plug-ins and finally a message like this:

```md
airflow-init-1 exited with code 0

The account created has the login airflow and the password airflow.
```

Build with custom dependencies. Rebuild at every update requirements.txt
```bash
docker build . --tag extending_airflow:latest # for build extended image with our packages
docker compose up -d --no-deps --build airflow-apiserver airflow-scheduler
```

Data quality monitoring helps find parsing errors: 
{"total_routes": 2, "total_flights_processed": 132, "merged_quality": {"total_flights": 132, "valid_flights": 66, "invalid_flights": 66, "partial_flights": 66, "completeness_scores": [], "missing_fields_summary": {}, "invalid_fields_summary": {"price": 66, "duration": 66}, "warnings_summary": {"Transformation error: argument of type 'NoneType' is not iterable": 66, "Invalid duration format: 1h 30m": 48, "Invalid price format: RUB 7,825": 16, "Invalid price format: RUB 4,425": 16, "Invalid price format: RUB 7,022": 12, "Invalid price format: RUB 5,534": 10, "Invalid price format: RUB 6,252": 8, "Invalid duration format: 1h 25m": 8, "Invalid duration format: 1h 35m": 6, "Invalid price format: RUB 4,808": 4, "Invalid duration format: 1h 40m": 4}, "overall_completeness": 0.5, "overall_quality": "poor"}, "route_statistics": {"avg_flights_per_route": 66.0, "min_flights_per_route": 64, "max_flights_per_route": 68, "std_flights_per_route": 2.83, "avg_completeness_per_route": 0.5, "min_completeness_per_route": 0.5, "max_completeness_per_route": 0.5, "route_quality_distribution": {"poor": 2}, "most_common_quality": "poor"}, "quality_ratios": {"valid_flights_ratio": 0.5, "partial_flights_ratio": 0.5, "invalid_flights_ratio": 0.5, "completeness_ratio": 0.5}, "field_issues": {"total_missing_field_occurrences": 0, "total_invalid_field_occurrences": 132, "total_warnings": 198, "top_missing_fields": {}, "top_invalid_fields": {"price": 66, "duration": 66}, "top_warnings": {"Transformation error: argument of type 'NoneType' is not iterable": 66, "Invalid duration format: 1h 30m": 48, "Invalid price format: RUB 7,825": 16, "Invalid price format: RUB 4,425": 16, "Invalid price format: RUB 7,022": 12, "Invalid price format: RUB 5,534": 10, "Invalid price format: RUB 6,252": 8, "Invalid duration format: 1h 25m": 8, "Invalid duration format: 1h 35m": 6, "Invalid price format: RUB 4,808": 4}}} 