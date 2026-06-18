# MD Data Pipeline

End-to-end ELT pipeline for Moldovan public data (BNM official exchange rates),
built with Python, PostgreSQL, dbt, and Airflow, fully containerized with Docker.

## Setup

> Work in progress — full instructions are added phase by phase.

1. Copy the environment template and fill in your values:

   ```bash
   cp .env.example .env
   ```

2. Start the local stack (PostgreSQL + Adminer):

   ```bash
   docker compose up -d
   ```

3. Open Adminer at http://localhost:8080 and log in with the credentials
   from your `.env` file (system: PostgreSQL, server: `postgres`).

## Ingestion (manual run)

Extract official exchange rates from the BNM public API and load them into the
`raw` schema. With the stack running (step 2 above):

```bash
pip install -r ingestion/requirements.txt

# Load a specific date (DD.MM.YYYY); omit --date to load today.
python ingestion/load_raw.py --date 18.06.2026
```

The loader reads database credentials from `.env` (or real environment
variables) and is idempotent — re-running the same date updates rows instead of
duplicating them.

Verify the rows landed (in Adminer, or via psql):

```sql
SELECT * FROM raw.exchange_rates ORDER BY char_code LIMIT 20;
```

## Transformations (dbt)

The `dbt/` project transforms `raw.exchange_rates` through
`staging -> intermediate -> marts`, all materialized in the `analytics` schema.
dbt reads the database connection from the same environment variables as the
ingestion step.

```bash
# Isolated environment (recommended)
python -m venv .venv
.venv/Scripts/python -m pip install dbt-postgres   # Windows
# source .venv/bin/activate                         # Linux/macOS

# Load DB credentials, then build and test from the dbt/ directory
cd dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
```

Inspect the final mart:

```sql
SELECT * FROM analytics.fct_daily_rates ORDER BY char_code, rate_date LIMIT 20;
```

## Orchestration (Airflow)

Apache Airflow (LocalExecutor) orchestrates the pipeline as a single DAG,
`md_pipeline`: `extract_and_load -> dbt_run -> dbt_test`, scheduled `@daily`.
Airflow has its own metadata database, separate from the data warehouse. Inside
the Docker network the tasks reach the data warehouse at `postgres:5432`.

Bring up the full stack (Postgres, Adminer, Airflow):

```bash
docker compose up -d --build
```

Open the Airflow UI at http://localhost:8081 and log in with
`AIRFLOW_ADMIN_USERNAME` / `AIRFLOW_ADMIN_PASSWORD` from your `.env`. Enable the
`md_pipeline` DAG and press Trigger to run it; all three tasks should turn green.

The DAG passes each run's logical date into ingestion (as `DD.MM.YYYY`), so
backfilling a past day works and stays idempotent. You can also run a single
date end to end from the command line:

```bash
docker compose exec airflow-scheduler airflow dags test md_pipeline 2026-06-18
```

| Service | URL | Notes |
|---|---|---|
| Airflow UI | http://localhost:8081 | DAG runs and logs |
| Adminer | http://localhost:8080 | Browse `raw` and `analytics` schemas |
