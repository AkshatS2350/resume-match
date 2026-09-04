"""The single migration set creates only the approved public-job schema."""

from pathlib import Path

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config


def test_alembic_upgrade_creates_the_five_approved_tables(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'public-jobs.sqlite3'}"
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert tables == {
        "alembic_version",
        "job_posting",
        "job_requirement",
        "job_skill",
        "job_education_req",
        "source_registry_state",
    }
