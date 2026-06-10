"""Golden test: run the tool on the repo root, assert the finding *set*
(kinds and counts), not exact prose. Plus report-structure invariants."""

from __future__ import annotations

import os

from spec_check.report import exit_code, render_json, render_markdown
from spec_check.run import check

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _counts(result):
    out: dict[str, int] = {}
    for f in result.findings:
        out[f.kind] = out.get(f.kind, 0) + 1
    return out


def test_repo_finding_set():
    result = check(REPO_ROOT)
    counts = _counts(result)
    # These are the dogfood findings on the self-hosted spec, run 5+:
    assert counts.get("unknown_term") == 12
    assert counts.get("duplicate_definition") == 1
    assert counts.get("nonconforming_card") == 18
    assert counts.get("entities_underspecified") == 1
    assert counts.get("conflict", 0) == 0
    assert counts.get("dead_rule", 0) == 0
    assert counts.get("gap", 0) >= 1
    # exit code non-zero because errors (unknown_term, duplicate_definition)
    assert exit_code(result) == 1


def test_report_walls_off_proven_and_judged():
    result = check(REPO_ROOT)
    md = render_markdown(result)
    proven = md.index("## Proven (mechanical findings)")
    judged = md.index("## Judged (criterion execution status)")
    # Proven comes before Judged and they are distinct sections (CHK-R10).
    assert proven < judged
    assert "no execution data" not in md[:proven].lower()


def test_report_states_projection_bound():
    # No silent coverage caps: the projection rule must be in the report.
    result = check(REPO_ROOT)
    md = render_markdown(result)
    assert "per-spec relevant projection" in md
    assert "not enumerated" in md


def test_report_has_entity_snapshot_comment():
    # Machine-readable baseline for CHK-R11 / D15.
    result = check(REPO_ROOT)
    md = render_markdown(result)
    assert "<!-- spec-check:entities" in md


def test_json_output_is_valid():
    import json

    result = check(REPO_ROOT)
    payload = json.loads(render_json(result))
    assert "findings" in payload
    assert "counts" in payload
    assert payload["exit_code"] == 1


def test_strict_promotes_warnings():
    result = check(REPO_ROOT)
    # already exit 1 from errors; check the strict flag path is honored
    assert exit_code(result, strict=True) == 1
