"""Create the approved five-table Public_Job_Data schema."""

from alembic import op
from resumematch.job.store.schema import metadata

revision = "20260904_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create only the approved public-job tables and indexes."""
    metadata.create_all(op.get_bind())


def downgrade() -> None:
    """Remove the public-job tables in dependency-safe metadata order."""
    metadata.drop_all(op.get_bind())
