from pathlib import Path

import pytest

from resumematch.skill.alias_loader import AliasConfigError, load_aliases


def test_loads_versioned_entries_with_required_fields() -> None:
    ontology = Path(__file__).resolve().parents[4] / "ontology" / "skills.yaml"
    aliases = load_aliases(ontology)
    assert aliases.version == "skills@1"
    assert all(
        entry.identifier and entry.display and entry.categories and entry.aliases
        for entry in aliases.entries
    )


def test_duplicate_folded_alias_names_both_entries(tmp_path: Path) -> None:
    path = tmp_path / "skills.yaml"
    path.write_text(
        "\n".join(
            (
                "version: skills@1", "skills:", "  - id: python", "    display: Python",
                "    categories: [language]", "    aliases: [py]", "  - id: pypi",
                "    display: PyPI", "    categories: [tool]", "    aliases: [PY]", "",
            )
        ),
        encoding="utf-8",
    )
    with pytest.raises(AliasConfigError, match="python.*pypi"):
        load_aliases(path)
