"""The persisted-column gate must reject a new candidate-derived database field."""

import runpy
from pathlib import Path

from sqlalchemy import Column, Text

from resumematch.job.store.schema import metadata


def test_persisted_column_gate_reports_an_unapproved_candidate_column() -> None:
    checker = runpy.run_path(
        str(Path(__file__).parents[3] / "tools" / "check_persisted_columns.py")
    )
    candidate_column = Column("candidate_profile_json", Text)
    metadata.tables["job_posting"].append_column(candidate_column)
    try:
        result = checker["find_unapproved_columns"](metadata)
    finally:
        metadata.tables["job_posting"]._columns.remove(candidate_column)

    assert result == {("job_posting", "candidate_profile_json")}
