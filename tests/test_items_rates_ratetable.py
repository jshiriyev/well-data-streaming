# test_rates.py
# Run: pytest -q
import datetime as dt
import pytest

# Adjust this import to your actual module filename
from wellx.items import RateTable


# ---------- Helpers ----------
def d(y, m, day):
    return dt.date(y, m, day)


# ---------- Schema ----------
def test_fields_schema():
    assert RateTable.fields() == [
        "well", "date", "days", "horizon", "otype", "choke", "orate", "wrate", "grate"
    ]