import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _copy_fixture(name: str, dest_dir: Path) -> None:
    shutil.copy(FIXTURES_DIR / name, dest_dir / name)


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _copy_fixture("wells.geojson", data_dir)
    _copy_fixture("rates.csv", data_dir)
    return data_dir


@pytest.fixture
def client_factory(monkeypatch):
    @contextmanager
    def _factory(data_dir: Path):
        monkeypatch.setenv("DATA_DIR", str(data_dir))
        monkeypatch.delenv("LOAD_DOTENV", raising=False)
        with TestClient(app) as client:
            yield client
    return _factory


@pytest.fixture
def client(sample_data_dir: Path, client_factory):
    with client_factory(sample_data_dir) as client:
        yield client
