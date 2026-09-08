from resumematch.core.schemas.rubric import Signal
from resumematch.rubric.resolvers import RESOLVERS, ResolvedSignal


def test_resolver_registry_has_exactly_one_entry_for_each_closed_signal_type() -> None:
    assert set(RESOLVERS) == {"skill", "experience_band", "education", "certification", "flag"}
    assert all(resolver.signal_type == signal_type for signal_type, resolver in RESOLVERS.items())


def test_resolved_signal_records_only_engine_consumed_evidence_fields() -> None:
    resolved = ResolvedSignal(
        evidence_level=2,
        determinability="determinable",
        supporting_item_ids=("item-1",),
    )

    assert resolved.evidence_level == 2
    assert resolved.determinability == "determinable"
    assert isinstance(
        Signal(
            signal_id="signal-1",
            type="skill",
            target={"target_type": "canonical_skill", "target_id": "python"},
            weight=1,
            min_evidence_level=1,
            required=False,
        ),
        Signal,
    )
