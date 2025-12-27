FROM apache/airflow:3.1.3
COPY requirements.txt /requirements.txt

USER root

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

RUN cp /usr/bin/chromedriver /home/airflow/chromedriver \
    && chown airflow /home/airflow/chromedriver \
    && chmod 755 /home/airflow/chromedriver

USER airflow

RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt

COPY db/ /opt/airflow/db/
COPY utils/ /opt/airflow/utils/
COPY scrapers/ /opt/airflow/scrapers/
COPY minio_utils/ /opt/airflow/minio_utils
COPY transformers/ /opt/airflow/transformers

# Set PYTHONPATH environment variable
ENV PYTHONPATH=/opt/airflow:$PYTHONPATH