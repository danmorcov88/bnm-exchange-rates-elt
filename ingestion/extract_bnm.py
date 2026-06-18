"""Extract official exchange rates from the BNM public XML API.

The endpoint returns a daily snapshot of official MDL exchange rates as XML:

    https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=DD.MM.YYYY

Only ``requests`` and the standard library are used.
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import requests

BNM_URL = "https://www.bnm.md/en/official_exchange_rates"
BNM_DATE_FORMAT = "%d.%m.%Y"
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class ExchangeRate:
    """A single currency rate as published by the BNM for a given date."""

    rate_date: date
    char_code: str
    num_code: str
    nominal: int
    name: str
    value: Decimal


class BNMError(RuntimeError):
    """Raised when the BNM API cannot be reached or returns unusable data."""


def parse_date_arg(value: str) -> date:
    """Parse a ``DD.MM.YYYY`` string into a date, with a clear error message."""
    try:
        return datetime.strptime(value, BNM_DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(f"Date must be in DD.MM.YYYY format, got: {value!r}") from exc


def fetch_raw_xml(target_date: date) -> str:
    """Call the BNM endpoint for a date and return the raw XML body."""
    params = {"get_xml": 1, "date": target_date.strftime(BNM_DATE_FORMAT)}
    try:
        response = requests.get(BNM_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BNMError(
            f"Failed to fetch BNM rates for {target_date.strftime(BNM_DATE_FORMAT)}: {exc}"
        ) from exc
    return response.text


def parse_rates(xml_text: str) -> list[ExchangeRate]:
    """Parse the BNM XML body into a list of ExchangeRate records."""
    if not xml_text or not xml_text.strip():
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise BNMError(f"Invalid XML received from BNM: {exc}") from exc

    date_attr = root.get("Date")
    if not date_attr:
        # An empty/holiday response has no Date attribute and no currencies.
        return []
    rate_date = datetime.strptime(date_attr, BNM_DATE_FORMAT).date()

    rates: list[ExchangeRate] = []
    for valute in root.findall("Valute"):
        char_code = (valute.findtext("CharCode") or "").strip().upper()
        if not char_code:
            continue
        raw_value = (valute.findtext("Value") or "").strip()
        raw_nominal = (valute.findtext("Nominal") or "").strip()
        try:
            value = Decimal(raw_value)
            nominal = int(raw_nominal)
        except (InvalidOperation, ValueError) as exc:
            raise BNMError(
                f"Could not parse value/nominal for {char_code}: "
                f"value={raw_value!r} nominal={raw_nominal!r} ({exc})"
            ) from exc
        rates.append(
            ExchangeRate(
                rate_date=rate_date,
                char_code=char_code,
                num_code=(valute.findtext("NumCode") or "").strip(),
                nominal=nominal,
                name=(valute.findtext("Name") or "").strip(),
                value=value,
            )
        )
    return rates


def extract_rates(target_date: date | None = None) -> list[ExchangeRate]:
    """Fetch and parse the BNM rates for a date (default: today)."""
    if target_date is None:
        target_date = date.today()
    return parse_rates(fetch_raw_xml(target_date))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch BNM exchange rates and print a summary (no DB writes)."
    )
    parser.add_argument(
        "--date",
        help="Target date in DD.MM.YYYY format (default: today).",
    )
    args = parser.parse_args()

    target_date = parse_date_arg(args.date) if args.date else date.today()
    rates = extract_rates(target_date)
    if not rates:
        print(f"No rates returned by BNM for {target_date.strftime(BNM_DATE_FORMAT)}.")
        return 0

    print(f"Fetched {len(rates)} rates for {rates[0].rate_date.isoformat()}:")
    for rate in rates[:5]:
        print(f"  {rate.char_code} {rate.nominal:>3} -> {rate.value}")
    if len(rates) > 5:
        print(f"  ... and {len(rates) - 5} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
