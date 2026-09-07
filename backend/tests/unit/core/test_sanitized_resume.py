from resumematch.core.schemas.candidate import StructuredResume
from resumematch.core.schemas.sanitized import SanitizedResume


def test_sanitized_resume_is_frozen_and_contains_only_category_counts() -> None:
    resume = StructuredResume(
        schema_version="structured_resume/1",
        summary="[[EMAIL]]",
        skills=(),
        experience=(),
        education=(),
        projects=(),
        certifications=(),
        achievements=(),
        unclassified=(),
    )

    sanitized = SanitizedResume(
        schema_version="sanitized_resume/1",
        source_profile_revision=2,
        resume=resume,
        target=None,
        removed_span_counts={"email": 1},
    )

    assert sanitized.source_profile_revision == 2
    assert sanitized.removed_span_counts == {"email": 1}
