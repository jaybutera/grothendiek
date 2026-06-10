"""CHK-R13 / T9: the unstratified_guard lint catches the liar shape."""

from __future__ import annotations

import os

from spec_check.run import check

LIAR_SPEC = """---
spec: liar
vocabulary:
  event: [check_run]
  finding.gap: [emitted, none]
  charge: [yes, no]
---

# Liar

## LIAR-R1: fires when no gap is found
when: event = check_run and finding.gap = none
then: charge = no — guard reads a finding variable: the liar shape

## LIAR-I1 (invariant): invariants may mention findings
invariant: finding.gap != emitted — claims about outputs are exempt (T9)
"""


def test_unstratified_guard_fires_on_liar(tmp_path):
    os.makedirs(tmp_path / "specs")
    (tmp_path / "specs" / "liar.md").write_text(LIAR_SPEC)
    result = check(str(tmp_path))
    hits = [f for f in result.findings if f.kind == "unstratified_guard"]
    assert len(hits) == 1
    assert "LIAR-R1" in hits[0].message
    assert "finding.gap" in hits[0].message
    # the invariant card is exempt (claim, not rule)
    assert "LIAR-I1" not in hits[0].message


def test_clean_guard_passes(tmp_path):
    os.makedirs(tmp_path / "specs")
    (tmp_path / "specs" / "ok.md").write_text(
        """---
spec: ok
vocabulary:
  event: [check_run]
  finding.gap: [emitted, none]
---

# OK

## OK-R1: writes findings, never reads them
when: event = check_run
then: finding.gap = emitted — write-side mention is the lawful direction
"""
    )
    result = check(str(tmp_path))
    assert not [f for f in result.findings if f.kind == "unstratified_guard"]
