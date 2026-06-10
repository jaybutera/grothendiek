"""Totality of the theory over the language surface (D19).

Not per-card — cards are programs, the theory is about the language. This
test enumerates the language's construct inventory from the code and the
spec-config, and asserts every construct appears in a backticked token of
specs/theory.md. Add a construct without founding it and this goes red.
"""

from __future__ import annotations

import os
import re

import yaml

from spec_check.model import CardKind

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _theory_tokens() -> set[str]:
    text = open(os.path.join(REPO_ROOT, "specs", "theory.md")).read()
    return set(re.findall(r"`([^`]+)`", text))


def _finding_kinds() -> set[str]:
    """The finding kinds are spec-config (D18): read them from the spec."""
    text = open(os.path.join(REPO_ROOT, "specs", "checking.md")).read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = yaml.safe_load(m.group(1))
    sev = fm["severities"]
    return set(sev.get("error", [])) | set(sev.get("warning", []))


def test_every_card_kind_is_founded():
    tokens = _theory_tokens()
    for kind in CardKind:
        name = kind.value.replace("_", "-")
        assert name in tokens, f"card kind '{name}' has no theory statement"


def test_every_finding_kind_is_founded():
    tokens = _theory_tokens()
    for kind in sorted(_finding_kinds()):
        assert kind in tokens, f"finding kind '{kind}' has no theory statement"


def test_core_language_constructs_are_founded():
    tokens = _theory_tokens()
    for construct in [
        "touching",
        "governing",
        "frame",
        "entity",
        "artifact",
        "baseline",
        "severities",
        "spec_commit",
        "work_review",
        "unchanged",
        "overrides",
        "coverage",
        "projection",
    ]:
        assert construct in tokens, f"construct '{construct}' unfounded"
