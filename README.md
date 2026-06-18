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
