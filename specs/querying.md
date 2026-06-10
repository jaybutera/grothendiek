---
spec: querying
imports:
  - from: core
    use: [Requirement, Decision, Footprint]
vocabulary:
  query.mode: [touching, governing]
  card.footprint_vs_region: [disjoint, intersects, contains]
  card.kind: [requirement, criterion]
  card.has_because: [yes, no]
  result.included: [yes, no]
  result.marked: [none, criterion]
  result.includes_rationale: [yes, no]
---

# Querying

`spec query <region>` is how a builder agent (or the designer) pulls the
commitments relevant to a piece of work before touching it. A region is a
guard-like predicate over vocabulary terms, or a set of glossary topics for
prose cards.

There are exactly two modes — the existential and universal images of the
region (the two adjoints of restriction; see [[D4]]).

## QRY-R1: touching mode returns everything that might bear on the work
when: event = query_run and query.mode = touching and card.footprint_vs_region = intersects
then: result.included = yes — the card is in the result
because: [[D4]]

## QRY-R2: touching mode also returns containing cards
when: event = query_run and query.mode = touching and card.footprint_vs_region = contains
then: result.included = yes — containing cards bear on the work too

## QRY-R3: governing mode returns only cards covering the whole region
when: event = query_run and query.mode = governing and card.footprint_vs_region = contains
then: result.included = yes — cards that merely intersect are excluded in
      governing mode
because: [[D4]]

## QRY-R4: results carry their rationale
when: event = query_run and card.has_because = yes
then: result.includes_rationale = yes — the linked Decisions appear in
      the result with their rationale and rejected alternatives, so an
      agent can argue with a rule, not just obey or silently break it

## QRY-R6: disjoint cards are not in the result
when: event = query_run and card.footprint_vs_region = disjoint
then: result.included = no — a card whose footprint shares nothing with
      the region has no bearing on the work

## QRY-R7: merely-intersecting cards are excluded in governing mode
when: event = query_run and query.mode = governing and
      card.footprint_vs_region = intersects
then: result.included = no — governing mode returns only cards covering
      the whole region (the universal adjoint); this card belongs to
      touching mode (QRY-R1)
because: [[D4]]

## QRY-R5: criteria are returned, and marked as such
when: event = query_run and card.kind = criterion and
      card.footprint_vs_region != disjoint
then: result.marked = criterion — the card is included per QRY-R1–R3, so a
      builder agent sees its review obligations alongside the requirements,
      but never mistakes a judgment for a theorem
because: [[D11]]

---

## D4 (decision, 2026-06-10): exactly two query modes
`--touching` (footprint ∩ region ≠ ∅) and `--governing` (footprint ⊇
region). These are the left and right adjoints of restricting the spec
presheaf along the region's inclusion — meaning there are exactly two
natural semantics, so new modes are prohibited unless this decision is
superseded with a semantics argument. **Rejected:** relevance scores /
fuzzy ranking as a third mode — ranking may order results *within* a mode
but never changes membership.
