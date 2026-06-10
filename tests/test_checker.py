"""Tests for checking semantics: frame desugaring, conflict, gap, dead_rule,
unknown_term, stale refs, duplicate definitions, orphan specs."""

from __future__ import annotations

import os

from spec_check import checker as C
from spec_check.model import (
    UNCHANGED,
    Card,
    CardKind,
    Clause,
    Effect,
    EffectKind,
    Guard,
    Op,
)
from spec_check.run import check

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _kinds(result):
    out: dict[str, int] = {}
    for f in result.findings:
        out[f.kind] = out.get(f.kind, 0) + 1
    return out


# --- frame desugaring -----------------------------------------------------


def test_frame_desugar_adds_unchanged():
    card = Card(
        kind=CardKind.REQUIREMENT,
        card_id="R1",
        title="t",
        spec="s",
        line=1,
        guard=Guard((Clause("sub.state", Op.EQ, "paused"),)),
        effects=(Effect("sub.state", EffectKind.TRANSITION, "paused"),),
        frame="sub",
    )
    entity_vars = {"sub": ["sub.state", "sub.price", "sub.notes"]}
    eff = C.desugar_frame(card, entity_vars, {})
    by_var = {e.variable: e.value for e in eff}
    assert by_var["sub.state"] == "paused"  # explicit, not overwritten
    assert by_var["sub.price"] == UNCHANGED
    assert by_var["sub.notes"] == UNCHANGED


def test_frame_unchanged_clashes_with_concrete():
    # one card freezes sub.price, another sets it -> conflict via D9
    a = C._Req(
        "s1",
        Card(CardKind.REQUIREMENT, "A", "", "s1", 1,
             guard=Guard((Clause("sub.state", Op.EQ, "paused"),))),
        C.R.cube_from_clauses({"sub.state": "paused"}, {},
                              {"sub.state": ("paused", "active")}),
        (Effect("sub.price", EffectKind.TRANSITION, UNCHANGED),),
    )
    b = C._Req(
        "s2",
        Card(CardKind.REQUIREMENT, "B", "", "s2", 1,
             guard=Guard((Clause("sub.state", Op.EQ, "paused"),))),
        C.R.cube_from_clauses({"sub.state": "paused"}, {},
                              {"sub.state": ("paused", "active")}),
        (Effect("sub.price", EffectKind.TRANSITION, "higher"),),
    )
    result = C.CheckResult()
    C.check_conflicts([a, b], {"sub.state": ("paused", "active")}, result)
    assert _kinds(result).get("conflict") == 1


def test_frame_unchanged_compatible_with_itself():
    dom = {"sub.state": ("paused", "active")}
    a = C._Req("s1", Card(CardKind.REQUIREMENT, "A", "", "s1", 1),
               C.R.cube_from_clauses({"sub.state": "paused"}, {}, dom),
               (Effect("sub.price", EffectKind.TRANSITION, UNCHANGED),))
    b = C._Req("s2", Card(CardKind.REQUIREMENT, "B", "", "s2", 1),
               C.R.cube_from_clauses({"sub.state": "paused"}, {}, dom),
               (Effect("sub.price", EffectKind.TRANSITION, UNCHANGED),))
    result = C.CheckResult()
    C.check_conflicts([a, b], dom, result)
    assert "conflict" not in _kinds(result)


# --- conflict / overrides -------------------------------------------------


def test_overrides_suppresses_conflict():
    dom = {"x": ("p", "q"), "y": ("a", "b")}
    ca = Card(CardKind.REQUIREMENT, "A", "", "s", 1, overrides=("B",))
    cb = Card(CardKind.REQUIREMENT, "B", "", "s", 1)
    a = C._Req("s", ca, C.R.cube_from_clauses({"x": "p"}, {}, dom),
               (Effect("y", EffectKind.RESPONSE, "a"),))
    b = C._Req("s", cb, C.R.cube_from_clauses({"x": "p"}, {}, dom),
               (Effect("y", EffectKind.RESPONSE, "b"),))
    result = C.CheckResult()
    C.check_conflicts([a, b], dom, result)
    assert "conflict" not in _kinds(result)


def test_disjoint_effects_compose_no_conflict():
    dom = {"x": ("p", "q"), "y": ("a", "b"), "z": ("a", "b")}
    a = C._Req("s", Card(CardKind.REQUIREMENT, "A", "", "s", 1),
               C.R.cube_from_clauses({"x": "p"}, {}, dom),
               (Effect("y", EffectKind.RESPONSE, "a"),))
    b = C._Req("s", Card(CardKind.REQUIREMENT, "B", "", "s", 1),
               C.R.cube_from_clauses({"x": "p"}, {}, dom),
               (Effect("z", EffectKind.RESPONSE, "b"),))
    result = C.CheckResult()
    C.check_conflicts([a, b], dom, result)
    assert "conflict" not in _kinds(result)


def test_nonoverlapping_guards_no_conflict():
    dom = {"x": ("p", "q"), "y": ("a", "b")}
    a = C._Req("s", Card(CardKind.REQUIREMENT, "A", "", "s", 1),
               C.R.cube_from_clauses({"x": "p"}, {}, dom),
               (Effect("y", EffectKind.RESPONSE, "a"),))
    b = C._Req("s", Card(CardKind.REQUIREMENT, "B", "", "s", 1),
               C.R.cube_from_clauses({"x": "q"}, {}, dom),
               (Effect("y", EffectKind.RESPONSE, "b"),))
    result = C.CheckResult()
    C.check_conflicts([a, b], dom, result)
    assert "conflict" not in _kinds(result)


# --- fixture-level integration -------------------------------------------


def test_billing_conflict_fixture():
    result = check(os.path.join(FIXTURES, "billing_conflict"))
    k = _kinds(result)
    assert k.get("conflict") == 1
    conflict = [f for f in result.findings if f.kind == "conflict"][0]
    assert conflict.witness is not None
    assert "suspended" in conflict.witness
    assert "payment_retry" in conflict.witness


def test_dead_rule_fixture():
    result = check(os.path.join(FIXTURES, "dead_rule"))
    k = _kinds(result)
    assert k.get("dead_rule") == 1
    dr = [f for f in result.findings if f.kind == "dead_rule"][0]
    assert "LIFE-R1" in dr.message
    assert "LIFE-I1" in dr.message


def test_all_findings_fixture_provokes_each_kind():
    result = check(os.path.join(FIXTURES, "all_findings"))
    k = _kinds(result)
    for kind in (
        "conflict",
        "gap",
        "dead_rule",
        "unknown_term",
        "duplicate_definition",
        "stale_decision_ref",
        "orphan_spec",
        "nonconforming_card",
    ):
        assert k.get(kind, 0) >= 1, f"missing {kind}: {k}"


def test_clean_fixture_no_findings():
    result = check(os.path.join(FIXTURES, "clean"))
    assert result.findings == [], _kinds(result)


def test_every_finding_has_a_pointer():
    # CHK-I1: no finding without a witness or location.
    for fx in ("billing_conflict", "dead_rule", "all_findings"):
        result = check(os.path.join(FIXTURES, fx))
        for f in result.findings:
            assert f.pointer_kind != "none", (fx, f.kind, f.message)
