"""The explicitly permitted v1 job-source catalog, with no transport behavior."""

from resumematch.job.source_api import SourceCapabilities

_PERMITTED_SOURCES = (
    SourceCapabilities(
        source_id="greenhouse",
        universal_search=False,
        requires_registry_entry=True,
        supports_incremental=False,
        is_network_source=True,
        documentation_url="https://developers.greenhouse.io/job-board.html",
        rate_limit_note=None,
    ),
    SourceCapabilities(
        source_id="lever",
        universal_search=False,
        requires_registry_entry=True,
        supports_incremental=False,
        is_network_source=True,
        documentation_url="https://github.com/lever/postings-api",
        rate_limit_note=None,
    ),
    SourceCapabilities(
        source_id="ashby",
        universal_search=False,
        requires_registry_entry=True,
        supports_incremental=False,
        is_network_source=True,
        documentation_url="https://developers.ashbyhq.com/docs/public-job-posting-api",
        rate_limit_note=None,
    ),
    SourceCapabilities(
        source_id="adzuna",
        universal_search=True,
        requires_registry_entry=False,
        supports_incremental=False,
        is_network_source=True,
        documentation_url="https://developer.adzuna.com/",
        rate_limit_note=None,
    ),
    SourceCapabilities(
        source_id="usajobs",
        universal_search=True,
        requires_registry_entry=False,
        supports_incremental=False,
        is_network_source=True,
        documentation_url="https://developer.usajobs.gov/",
        rate_limit_note=None,
    ),
    SourceCapabilities(
        source_id="fixture",
        universal_search=False,
        requires_registry_entry=False,
        supports_incremental=False,
        is_network_source=False,
        documentation_url="fixture://checked-in",
        rate_limit_note=None,
    ),
)


def permitted_sources() -> tuple[SourceCapabilities, ...]:
    """Return the stable v1 allowlist in display order."""
    return _PERMITTED_SOURCES
