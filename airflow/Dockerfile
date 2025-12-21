FROM apache/airflow:3.1.3
COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt

COPY db/ /opt/airflow/db/
COPY func/ /opt/airflow/func/
COPY scrapers/ /opt/airflow/scrapers/

# Set PYTHONPATH environment variable
ENV PYTHONPATH=/opt/airflow:$PYTHONPATH