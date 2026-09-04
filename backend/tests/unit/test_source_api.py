from dataclasses import fields


def test_source_capabilities_requires_a_documentation_url() -> None:
    from resumematch.job.source_api import SourceCapabilities

    assert "documentation_url" in {field.name for field in fields(SourceCapabilities)}


def test_raw_posting_is_distinct_from_validated_job_posting() -> None:
    from resumematch.job.source_api import RawPosting

    assert {field.name for field in fields(RawPosting)} == {"source_external_id", "payload"}
