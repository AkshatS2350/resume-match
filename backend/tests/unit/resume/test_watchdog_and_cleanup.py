import asyncio
import time
from pathlib import Path

import pytest

from resumematch.core.errors import ErrorCode, PipelineError
from resumematch.resume import upload


def test_watchdog_maps_slow_extraction_to_safe_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(upload, "EXTRACTION_TIMEOUT_SECONDS", 0.01)

    def slow(_: Path) -> object:
        time.sleep(0.1)
        return object()

    with pytest.raises(PipelineError) as raised:
        asyncio.run(upload.extract_with_watchdog(slow, tmp_path / "resume.pdf"))
    assert raised.value.code is ErrorCode.EXTRACTION_TIMEOUT
