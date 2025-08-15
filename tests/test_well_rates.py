# test_rates.py
# Run: pytest -q
import datetime as dt
import pytest

# Adjust this import to your actual module filename
from wellx.items import Rates


# ---------- Helpers ----------
def d(y, m, day):
    return dt.date(y, m, day)


# ---------- Schema ----------
def test_fields_schema():
    assert Rates.fields() == [
        "date", "days", "horizon", "optype", "choke", "orate", "wrate", "grate"
    ]