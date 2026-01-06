import json


def test_wells_date_filter(client):
    resp = client.get("/api/wells", params={"date": "2014-01-01"})
    assert resp.status_code == 200
    data = resp.json()
    names = {row["well"] for row in data}
    assert names == {"A-01"}


def test_wells_invalid_date_returns_422(client):
    resp = client.get("/api/wells", params={"date": "not-a-date"})
    assert resp.status_code == 422
    detail = resp.json().get("detail", [])
    assert any("date" in err.get("loc", []) for err in detail)


def test_wells_invalid_coordinates(sample_data_dir, client_factory):
    wells_path = sample_data_dir / "wells.geojson"
    payload = json.loads(wells_path.read_text(encoding="utf-8"))
    payload["features"][1]["geometry"]["coordinates"] = ["bad", 40.1]
    wells_path.write_text(json.dumps(payload), encoding="utf-8")

    with client_factory(sample_data_dir) as client:
        resp = client.get("/api/wells")

    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["error_count"] == 1
    assert detail["errors"][0]["code"] == "invalid_coordinates"
    assert detail["errors"][0]["index"] == 1
