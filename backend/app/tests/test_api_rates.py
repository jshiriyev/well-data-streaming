import os
import time

import pytest


def test_rates_default_sum(client):
    resp = client.get("/api/rates")
    assert resp.status_code == 200
    data = resp.json()

    dates = data["date"]
    idx = dates.index("2024-01-01")
    assert data["oil_rate"][idx] == pytest.approx(300.0)
    assert data["water_rate"][idx] == pytest.approx(110.0)
    assert data["gas_rate"][idx] == pytest.approx(2100.0)


def test_rates_custom_aggregation(client):
    resp = client.get(
        "/api/rates",
        params={"agg": ["oil_rate:mean", "water_rate:sum"]},
    )
    assert resp.status_code == 200
    data = resp.json()

    dates = data["date"]
    idx = dates.index("2024-01-01")
    assert data["oil_rate"][idx] == pytest.approx(150.0)
    assert data["water_rate"][idx] == pytest.approx(110.0)
    assert "gas_rate" not in data


def test_rates_date_filtering(client):
    resp = client.get(
        "/api/rates",
        params={"start": "2024-01-02", "end": "2024-01-03"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == ["2024-01-02", "2024-01-03"]


def test_rates_reload_on_file_change(sample_data_dir, client_factory):
    with client_factory(sample_data_dir) as client:
        resp = client.get("/api/rates")
        assert resp.status_code == 200
        assert "2024-02-01" in resp.json()["date"]

        rates_path = sample_data_dir / "rates.csv"
        with rates_path.open("a", encoding="utf-8") as handle:
            handle.write("\n2024-03-01,C-03,PK,300,70,1200")

        new_mtime = time.time() + 5
        os.utime(rates_path, (new_mtime, new_mtime))

        resp = client.get("/api/rates")
        assert resp.status_code == 200
        assert "2024-03-01" in resp.json()["date"]
