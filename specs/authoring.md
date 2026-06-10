---
spec: authoring
imports:
  - from: core
    use: [Spec, Requirement, Decision, Delta]
vocabulary:
  event: [gap_answered, delta_proposed, delta_approved, delta_rejected,
          decision_change_needed, agent_edit_planned]
  actor: [designer, builder_agent]
  delta.status: [proposed, approved, rejected]
  collision.with_active_decision: [yes, no]
---

# Authoring

How the spec grows and changes. The designer never has to open a spec file:
they answer questions in conversation; agents draft the cards; the designer
approves diffs. The spec is the accumulated, deduplicated residue of those
conversations.

## AUT-R1: gap answers become deltas, not edits
when: event = gap_answered and actor = designer
then: an agent drafts a Delta containing the new/changed requirement card
      (with guard, effects, and `because:` links) and presents it for
      approval; nothing merges on the designer's words alone
because: [[D11]]

## AUT-R2: only the designer approves deltas
when: event = delta_approved
then: the approving actor is the designer; builder agents may propose and
      revise deltas but never approve their own

## AUT-R3: decisions are superseded, never edited
when: event = decision_change_needed
then: a new Decision is recorded with a `supersedes:` link and its own
      rationale; the old card's text is untouched and its status becomes
      superseded
because: [[D6]]

## AUT-R4: agents query before editing
when: event = agent_edit_planned and actor = builder_agent
then: the agent runs `spec query --touching` over the work's region before
      modifying behavior, and treats the returned cards as constraints
because: [[D6]]

## AUT-R5: collisions stop the edit, with the rationale attached
when: event = agent_edit_planned and collision.with_active_decision = yes
then: the agent does not proceed; it surfaces the colliding Decision *and
      its rationale* to the designer, who may supersede it (AUT-R3) or
      withdraw the change
because: [[D6]]

## AUT-R6: operative content is checkable; prose carries rationale
when: event = delta_proposed
then: every requirement card in the delta has a guard and structured
      effects in vocabulary terms; every criterion card has a footprint
      and a declared evaluation procedure; explanation, motivation, and
      nuance go in prose, which never carries operative semantics
because: [[D11]]

---

## D5 (decision, 2026-06-10): prose-primary, minimal formal surface
status: superseded by [[D7]]
Designers are legitimately "lazy": demanding full formalization upfront is
how spec languages die. Formalize only the nouns, guards, and outcomes
needed for checking and querying; let English carry everything else, and
let the system's questions (CHK-R2) drive completion incrementally.
**Rejected:** full formal specs (TLA+/Alloy-style as the authoring format) —
the graveyard option.

## D7 (decision, 2026-06-10): no card without a check
supersedes: D5
status: superseded by [[D11]] (the mandate stands; the two-tier framing
became the requirement/criterion split in `specs/criteria.md`)
Expressiveness is bounded by checkability, deliberately: a card that
declares no check procedure cannot exist. Operative content (guard +
effects) is written in vocabulary terms, at one of two tiers — *mechanical*
(checked by enumeration over situation space) or *judged* (an agent
executes the card's declared evaluation procedure against an artifact;
verdicts are marked as judgment calls). Soft commitments stay expressible,
but only by reifying them into a judged criterion — declaring the check
procedure is itself most of the specification work. D5's core survives,
rescoped: prose carries rationale, motivation, and nuance — never operative
semantics — and the system's questions still drive incremental completion.
**Rejected:** optional structured effects — optional formality erodes (the
`any`-type dynamic): the unchecked path is locally cheaper at every step,
the checked core silently shrinks, and confidence in the checker inflates
while its actual coverage drops. (Designer's argument, 2026-06-10.)

## D6 (decision, 2026-06-10): decisions are first-class agent memory
The failure mode this system exists to prevent: agents silently overwriting
old decisions because they live nowhere explicit. So decisions are cards
with rationale and footprints, agents must consult them before editing, and
overriding one is always an explicit, designer-approved supersession.
**Rejected:** decisions as commit messages or chat history — not queryable
at edit time, and rationale gets lost.
