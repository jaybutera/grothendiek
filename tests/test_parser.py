"""Unit tests for the spec parser: frontmatter, guards, effects, cards."""

from __future__ import annotations

from spec_check.model import CardKind, EffectKind, Op
from spec_check.parser import (
    parse_effects,
    parse_guard,
    parse_spec,
    split_frontmatter,
)


def test_yaml_keeps_yes_no_as_strings():
    fm, _ = split_frontmatter(
        "---\nspec: x\nvocabulary:\n  a: [yes, no]\n  b: [on, off]\n---\nbody\n"
    )
    assert fm["vocabulary"]["a"] == ["yes", "no"]
    assert fm["vocabulary"]["b"] == ["on", "off"]


def test_split_frontmatter_none():
    fm, body = split_frontmatter("# no frontmatter\ntext\n")
    assert fm == {}
    assert "no frontmatter" in body


def test_parse_guard_conjunction():
    g, errs = parse_guard("event = check_run and sub.state != paused")
    assert errs == []
    assert g is not None
    assert len(g.clauses) == 2
    assert g.clauses[0].variable == "event"
    assert g.clauses[0].op == Op.EQ
    assert g.clauses[1].op == Op.NE
    assert g.clauses[1].value == "paused"


def test_parse_guard_unparseable_fragment():
    g, errs = parse_guard("event = check_run and an included Requirement has links")
    # first clause parses; the prose fragment is reported
    assert g is not None
    assert any("included Requirement" in e for e in errs)


def test_parse_guard_empty():
    g, errs = parse_guard("")
    assert g is None
    assert errs


def test_parse_effects_transition_and_response():
    eff, errs = parse_effects("sub.state -> paused, charge = no")
    assert errs == []
    assert len(eff) == 2
    assert eff[0].kind == EffectKind.TRANSITION
    assert eff[0].value == "paused"
    assert eff[1].kind == EffectKind.RESPONSE
    assert eff[1].value == "no"


def test_parse_effects_emdash_annotation():
    eff, errs = parse_effects("charge = yes — because the retry succeeded")
    assert errs == []
    assert len(eff) == 1
    assert eff[0].value == "yes"


def test_parse_effects_lenient_trailing_prose():
    # leading assignment parses; comma-prose without em-dash is annotation
    eff, errs = parse_effects("finding = conflict, naming both cards")
    assert errs == []
    assert len(eff) == 1
    assert eff[0].variable == "finding"
    assert eff[0].value == "conflict"


def test_parse_effects_no_leading_assignment_nonconforming():
    eff, errs = parse_effects("the card is included in the result")
    assert eff == ()
    assert errs == ["<no leading assignment>"]


SPEC_TEXT = """---
spec: billing
imports:
  - from: core
    use: [Requirement]
vocabulary:
  user.state: [active, suspended]
  charge: [yes, no]
entities:
  user: [user.state]
---

# Billing

## BILL-R1: suspended users are not charged
when: user.state = suspended
then: charge = no
frame: user
because: [[D9]]

## BILL-I1 (invariant): closed never charges
invariant: user.state != active — explanatory prose here

## D9 (decision, 2026-01-01): something
supersedes: D2
status: superseded by [[D12]]
"""


def test_parse_spec_cards():
    spec = parse_spec("billing.md", SPEC_TEXT)
    assert spec.name == "billing"
    assert spec.vocabulary["charge"] == ("yes", "no")
    assert spec.entities["user"] == ("user.state",)
    ids = {c.card_id: c for c in spec.cards}
    r1 = ids["BILL-R1"]
    assert r1.kind == CardKind.REQUIREMENT
    assert r1.frame == "user"
    assert r1.because == ("D9",)
    assert r1.guard.clauses[0].variable == "user.state"
    assert r1.effects[0].variable == "charge"
    inv = ids["BILL-I1"]
    assert inv.kind == CardKind.INVARIANT
    assert inv.invariant_guard is not None
    d9 = ids["D9"]
    assert d9.kind == CardKind.DECISION
    assert d9.supersedes == ("D2",)
    assert d9.superseded_by == ("D12",)


def test_overrides_parsed():
    text = """---
spec: x
vocabulary:
  a: [p, q]
---
## X-R1: a
when: a = p
then: a = q
overrides: X-R2
"""
    spec = parse_spec("x.md", text)
    r1 = [c for c in spec.cards if c.card_id == "X-R1"][0]
    assert r1.overrides == ("X-R2",)
