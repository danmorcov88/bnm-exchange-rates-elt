"""Daily ELT pipeline: extract BNM rates, load raw, then run and test dbt.

The DAG passes each run's logical date into the ingestion step (reformatted to
the BNM ``DD.MM.YYYY`` format), so manual triggers and backfills load the
correct day. The raw load is idempotent (ON CONFLICT), so re-running a date
never duplicates rows.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

AIRFLOW_HOME = "/opt/airflow"
DBT_BIN = "/opt/dbt-venv/bin/dbt"
DBT_DIR = f"{AIRFLOW_HOME}/dbt"

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="md_pipeline",
    description="Extract BNM exchange rates, load raw, then run and test dbt models.",
    schedule="@daily",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["bnm", "elt", "dbt"],
) as dag:

    extract_and_load = BashOperator(
        task_id="extract_and_load",
        bash_command=(
            f"python {AIRFLOW_HOME}/ingestion/load_raw.py "
            "--date {{ macros.ds_format(ds, '%Y-%m-%d', '%d.%m.%Y') }}"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} run --profiles-dir {DBT_DIR}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} test --profiles-dir {DBT_DIR}",
    )

    extract_and_load >> dbt_run >> dbt_test
