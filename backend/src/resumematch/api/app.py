"""Application-startup safeguards for the single-worker deployment model."""

import os

from resumematch.core.config import ConfigInvalid

_WORKER_COUNT_VARIABLES = (
    "WEB_CONCURRENCY",
    "UVICORN_WORKERS",
    "GUNICORN_WORKERS",
)


def ensure_single_worker() -> None:
    """Reject a worker configuration incompatible with process-local sessions."""

    for variable in _WORKER_COUNT_VARIABLES:
        value = os.environ.get(variable)
        if value is None:
            continue
        try:
            workers = int(value)
        except ValueError as error:
            raise ConfigInvalid(f"invalid worker count for {variable}") from error
        if workers > 1:
            raise ConfigInvalid(
                f"{variable} must be unset or 1 because ResumeMatch uses a "
                "process-local SessionStore"
            )


ensure_single_worker()
