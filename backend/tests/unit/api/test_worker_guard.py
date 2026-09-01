import pytest

from resumematch.api.app import ensure_single_worker
from resumematch.core.config import ConfigInvalid


@pytest.mark.parametrize("variable", ["WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"])
def test_rejects_multiple_workers(monkeypatch: pytest.MonkeyPatch, variable: str) -> None:
    monkeypatch.setenv(variable, "2")

    with pytest.raises(ConfigInvalid, match=variable):
        ensure_single_worker()


def test_allows_an_unset_or_single_worker_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in ("WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"):
        monkeypatch.delenv(variable, raising=False)

    ensure_single_worker()

    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    ensure_single_worker()
