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
