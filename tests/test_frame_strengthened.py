"""CHK-R11 / D15: frame_strengthened against a git REPORT.md baseline."""

from __future__ import annotations

import subprocess

import pytest

from spec_check import checker as C
from spec_check.run import _check_frame_strengthened, _read_baseline_entities


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def test_baseline_unavailable_without_git(tmp_path):
    result = C.CheckResult()
    result.entity_vars = {"sub": ["sub.state"]}
    _check_frame_strengthened(str(tmp_path), result, {"sub": ["R1"]})
    assert result.baseline_note is not None
    assert "baseline unavailable" in result.baseline_note
    assert not any(f.kind == "frame_strengthened" for f in result.findings)


def test_frame_strengthened_detected(tmp_path):
    root = str(tmp_path)
    _git(root, "init")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    report = tmp_path / "REPORT.md"
    report.write_text(
        "# old report\n\n<!-- spec-check:entities\n"
        "sub: sub.state\n-->\n"
    )
    _git(root, "add", "REPORT.md")
    _git(root, "commit", "-m", "baseline")

    baseline = _read_baseline_entities(root)
    assert baseline == {"sub": {"sub.state"}}

    result = C.CheckResult()
    # current vocabulary grew sub with a new attribute
    result.entity_vars = {"sub": ["sub.state", "sub.notes"]}
    _check_frame_strengthened(root, result, {"sub": ["R1"]})
    fs = [f for f in result.findings if f.kind == "frame_strengthened"]
    assert len(fs) == 1
    assert "sub.notes" in fs[0].message
    assert fs[0].location is not None


def test_no_frame_growth(tmp_path):
    root = str(tmp_path)
    _git(root, "init")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    report = tmp_path / "REPORT.md"
    report.write_text(
        "# old\n\n<!-- spec-check:entities\nsub: sub.state\n-->\n"
    )
    _git(root, "add", "REPORT.md")
    _git(root, "commit", "-m", "baseline")

    result = C.CheckResult()
    result.entity_vars = {"sub": ["sub.state"]}
    _check_frame_strengthened(root, result, {"sub": ["R1"]})
    assert not any(f.kind == "frame_strengthened" for f in result.findings)
    assert "no frame growth" in result.baseline_note


def test_unframed_entity_growth_is_silent(tmp_path):
    # CHK-R11: growth on an entity nothing frames strengthens no card.
    root = str(tmp_path)
    _git(root, "init")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    report = tmp_path / "REPORT.md"
    report.write_text(
        "# old\n\n<!-- spec-check:entities\nsub: sub.state\n-->\n"
    )
    _git(root, "add", "REPORT.md")
    _git(root, "commit", "-m", "baseline")

    result = C.CheckResult()
    result.entity_vars = {"sub": ["sub.state", "sub.notes"]}
    _check_frame_strengthened(root, result, {})
    assert not any(f.kind == "frame_strengthened" for f in result.findings)
