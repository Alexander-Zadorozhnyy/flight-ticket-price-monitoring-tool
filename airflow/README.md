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