FROM apache/airflow:2.10.5-python3.11

# Ingestion dependencies (light; psycopg2 ships with the postgres provider).
COPY ingestion/requirements.txt /tmp/ingestion-requirements.txt
RUN pip install --no-cache-dir -r /tmp/ingestion-requirements.txt

# dbt lives in its own virtualenv so its dependency pins never clash with
# Airflow's. The DAG calls /opt/dbt-venv/bin/dbt directly.
USER root
RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir --upgrade pip wheel \
    && /opt/dbt-venv/bin/pip install --no-cache-dir dbt-postgres \
    && chown -R airflow: /opt/dbt-venv
USER airflow
