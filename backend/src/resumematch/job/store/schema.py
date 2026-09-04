"""SQLAlchemy Core schema for the five approved Public_Job_Data tables."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

job_posting = Table(
    "job_posting",
    metadata,
    Column("internal_id", String, primary_key=True),
    Column("source_id", String, nullable=False),
    Column("source_external_id", String, nullable=False),
    Column("company", Text, nullable=False),
    Column("raw_title", Text, nullable=False),
    Column("raw_description", Text, nullable=False),
    Column("apply_url", Text, nullable=False),
    Column("normalized_title", Text),
    Column("role_family", String),
    Column("seniority", String),
    Column("normalized_location", Text),
    Column("raw_location", Text),
    Column("work_mode", String),
    Column("employment_type", String),
    Column("min_experience_years", Numeric(10, 2)),
    Column("max_experience_years", Numeric(10, 2)),
    Column("experience_conflict", Boolean, nullable=False),
    Column("posted_at", DateTime(timezone=True)),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Column("duplicate_group_id", String),
    Column("is_primary_in_group", Boolean, nullable=False),
    Column("pattern_set_version", String),
    Column("delimitation_version", String),
    Column("company_fold", Text, nullable=False),
    Column("title_fold", Text, nullable=False),
    Column("location_fold", Text, nullable=False),
    UniqueConstraint("source_id", "source_external_id"),
)
Index(
    "ix_job_posting_duplicate_folds",
    job_posting.c.company_fold,
    job_posting.c.title_fold,
    job_posting.c.location_fold,
)

job_requirement = Table(
    "job_requirement",
    metadata,
    Column("requirement_id", String, primary_key=True),
    Column("internal_id", String, ForeignKey("job_posting.internal_id"), nullable=False),
    Column("classification", String, nullable=False),
    Column("low_confidence", Boolean, nullable=False),
    Column("canonical_skill_id", String),
    Column("unit_text", Text, nullable=False),
    Column("start_offset", Integer, nullable=False),
    Column("end_offset", Integer, nullable=False),
    Column("unit_id", String, nullable=False),
    Column("excluded_category", String),
    CheckConstraint("end_offset > start_offset", name="ck_job_requirement_offsets"),
)

job_skill = Table(
    "job_skill",
    metadata,
    Column("internal_id", String, ForeignKey("job_posting.internal_id"), primary_key=True),
    Column("canonical_skill_id", String, primary_key=True),
    Column("kind", String, primary_key=True),
    CheckConstraint("kind IN ('required', 'preferred')", name="ck_job_skill_kind"),
)

job_education_req = Table(
    "job_education_req",
    metadata,
    Column("internal_id", String, ForeignKey("job_posting.internal_id"), primary_key=True),
    Column("degree_level", String, primary_key=True),
    Column("field_of_study", String, primary_key=True),
    Column("requirement_kind", String, primary_key=True),
    CheckConstraint("requirement_kind IN ('required', 'preferred')", name="ck_job_education_kind"),
)

source_registry_state = Table(
    "source_registry_state",
    metadata,
    Column("source_id", String, primary_key=True),
    Column("board_id", String, primary_key=True),
    Column("last_run_at", DateTime(timezone=True)),
    Column("postings_fetched", Integer, nullable=False),
    Column("postings_normalized", Integer, nullable=False),
    Column("postings_rejected", Integer, nullable=False),
    Column("failure_count", Integer, nullable=False),
)
