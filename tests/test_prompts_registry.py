"""Tests del registro de prompts versionado (src/prompts/registry.py)."""
from __future__ import annotations

import pytest

from src.prompts.registry import PROMPT_REGISTRY, get_prompt


def test_registry_prompts_are_versioned():
    assert PROMPT_REGISTRY, "el registro no puede estar vacío"
    for name, entry in PROMPT_REGISTRY.items():
        assert "version" in entry, f"{name} sin campo version"
        assert "changelog" in entry, f"{name} sin changelog"


def test_get_prompt_known_name():
    name = next(iter(PROMPT_REGISTRY))
    entry = get_prompt(name)
    assert entry["version"]


def test_get_prompt_unknown_name_raises():
    with pytest.raises(KeyError):
        get_prompt("prompt_inexistente")
