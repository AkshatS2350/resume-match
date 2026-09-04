from resumematch.core.schemas.candidate import SeniorityId


def test_company_fold_removes_legal_suffixes_and_punctuation() -> None:
    from resumematch.job.normalizer import company_fold

    assert company_fold("Northwind Systems, Inc.") == company_fold("northwind systems")


def test_title_fold_extracts_seniority() -> None:
    from resumematch.job.normalizer import title_fold

    assert title_fold("Senior Backend Engineer") == ("backend engineer", SeniorityId.SENIOR)


def test_location_fold_uses_configured_aliases() -> None:
    from resumematch.job.normalizer import location_fold

    assert location_fold("Austin, TX") == location_fold("Austin, Texas, US")
