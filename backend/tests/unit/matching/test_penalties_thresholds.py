from pathlib import Path

from resumematch.matching.config import load_penalties, load_thresholds


def test_penalties_and_thresholds_are_ordered() -> None:
    root = Path(__file__).resolve().parents[4] / "config"
    preferred, hard = load_penalties(root / "match_penalties.yaml")
    strong, stretch = load_thresholds(root / "match_thresholds.yaml")
    assert preferred < hard
    assert stretch < strong
