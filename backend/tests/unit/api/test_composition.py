from dataclasses import is_dataclass

import resumematch.api.composition as composition


def test_composition_constructs_core_collaborators_without_module_singletons() -> None:
    components = composition.build_components()

    assert is_dataclass(components)
    assert components.session_store is not None
    assert components.clock is not None
    assert not any(
        not name.startswith("_")
        and not callable(value)
        and value is not components.__class__
        and value is not None
        for name, value in vars(composition).items()
    )
