FROM python:3.12-slim

WORKDIR /visualization_app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos "" appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

USER appuser

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "./main.py"]