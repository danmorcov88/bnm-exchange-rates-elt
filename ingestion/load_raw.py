"""Load BNM exchange rates into the Postgres ``raw`` schema.

The load is idempotent: re-running the same date updates existing rows instead
of inserting duplicates, thanks to the ``(rate_date, char_code)`` primary key
and ``ON CONFLICT ... DO UPDATE``.

Database credentials are read from environment variables (POSTGRES_USER,
POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT). For convenience
when running on the host, a ``.env`` file at the project root is loaded if
present; real environment variables always take precedence.
"""
from __future__ import annotations

import argparse
import os
from datetime import date

import psycopg2
from psycopg2.extras import execute_values

from extract_bnm import ExchangeRate, extract_rates, parse_date_arg

CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS raw;"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS raw.exchange_rates (
    rate_date  date           NOT NULL,
    char_code  text           NOT NULL,
    num_code   text,
    nominal    integer        NOT NULL,
    name       text,
    value      numeric(18, 6) NOT NULL,
    loaded_at  timestamptz    NOT NULL DEFAULT now(),
    PRIMARY KEY (rate_date, char_code)
);
"""

UPSERT = """
INSERT INTO raw.exchange_rates
    (rate_date, char_code, num_code, nominal, name, value)
VALUES %s
ON CONFLICT (rate_date, char_code) DO UPDATE SET
    num_code  = EXCLUDED.num_code,
    nominal   = EXCLUDED.nominal,
    name      = EXCLUDED.name,
    value     = EXCLUDED.value,
    loaded_at = now();
"""


def load_dotenv(path: str | None = None) -> None:
    """Populate os.environ from a .env file without overriding existing vars."""
    if path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(project_root, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_connection():
    """Open a Postgres connection from environment variables."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def load_rates(rates: list[ExchangeRate]) -> int:
    """Upsert exchange-rate records into raw.exchange_rates. Returns row count."""
    if not rates:
        return 0
    rows = [
        (r.rate_date, r.char_code, r.num_code, r.nominal, r.name, r.value)
        for r in rates
    ]
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_SCHEMA)
                cur.execute(CREATE_TABLE)
                execute_values(cur, UPSERT, rows)
    finally:
        conn.close()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract BNM rates for a date and load them into raw.exchange_rates."
    )
    parser.add_argument(
        "--date",
        help="Target date in DD.MM.YYYY format (default: today).",
    )
    args = parser.parse_args()

    load_dotenv()
    target_date = parse_date_arg(args.date) if args.date else date.today()
    rates = extract_rates(target_date)
    if not rates:
        print(
            f"No rates returned by BNM for {target_date.strftime('%d.%m.%Y')}; "
            "nothing to load."
        )
        return 0

    count = load_rates(rates)
    print(
        f"Loaded {count} exchange rates for {rates[0].rate_date.isoformat()} "
        "into raw.exchange_rates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
