.DEFAULT_GOAL := help

.PHONY: help up down clean build logs ps test backfill ingest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

up: ## Build and start the full stack (Postgres, Adminer, Airflow)
	docker compose up -d --build

down: ## Stop the stack (keeps data)
	docker compose down

clean: ## Stop the stack and remove volumes (wipes data)
	docker compose down -v

logs: ## Tail logs from all services
	docker compose logs -f

ps: ## Show service status
	docker compose ps

test: ## Run dbt models and tests inside the Airflow image
	docker compose exec airflow-scheduler bash -lc "cd /opt/airflow/dbt && /opt/dbt-venv/bin/dbt build --profiles-dir ."

backfill: ## Run one date end to end, e.g. make backfill DATE=2026-06-17
	docker compose exec airflow-scheduler airflow dags test md_pipeline $(DATE)

ingest: ## Load raw rates for a date, e.g. make ingest DATE=17.06.2026
	docker compose exec airflow-scheduler python /opt/airflow/ingestion/load_raw.py --date $(DATE)
