---
spec: criteria
imports:
  - from: core
    use: [Criterion, Procedure, Verdict, Footprint]
vocabulary:
  event: [work_review]
  criterion.touched: [yes, no]      # work region ∩ criterion footprint ≠ ∅
  pair.contradictory: [yes, no]     # two touched criteria pull opposite ways
  pair.verdict_exists: [yes, no]
---

# Criteria

The judged layer, structurally separated from the spec proper ([[D11]]).
A **Criterion** is not a requirement: it is a review obligation attached to
a region — "whenever work touches this footprint, execute this procedure
and record the verdict." Requirements get theorems (conflict, gap,
dead-rule analysis); criteria get execution, verdicts, and audit trails.
The two are never processed by the same machinery, so they cannot be
mistaken for each other:

1. Criteria never count toward coverage — a region addressed only by a
   criterion is still a gap (CHK-R9 in `specs/checking.md`).
2. Criteria have no check-time conflict semantics — contradictions surface
   at execution (CRI-R2) and are settled by designer ruling, not by D9.
3. Check reports wall off Proven from Judged (CHK-R10).

## CRI-R1: touched criteria are executed
when: event = work_review and criterion.touched = yes
then: procedure.executed = yes, verdict.recorded = yes — the verdict is
      bound to the reviewed artifact (commit/PR), so staleness is
      detectable later
because: [[D11]]

## CRI-R2: contradictions escalate to the designer
when: event = work_review and pair.contradictory = yes and
      pair.verdict_exists = no
then: escalation = designer; the ruling is recorded as a Verdict card
      naming both criteria and the situation that exposed the tension
because: [[D11]]

## CRI-R3: rulings are remembered
when: event = work_review and pair.contradictory = yes and
      pair.verdict_exists = yes
then: the recorded Verdict applies; the pair is not re-raised to the
      designer
because: [[D11]]

---

## D11 (decision, 2026-06-10): requirements prove, criteria judge
supersedes: D7
D7's mandate stands — no card without a check, prose carries rationale
only — but "one card kind, two tiers" was the wrong shape: interleaving
judged content with mechanical content blurs confidence levels, and a
green report must mean *proven*, never *proven-ish* (designer's point,
2026-06-10). So judged cards become a distinct kind, **Criterion**
(footprint + procedure, no guard/effects), with deliberately different
semantics: no coverage contribution, no check-time conflict analysis,
contradictions settled at execution time as Verdict cards. Soft
commitments remain expressible — the D7 concern — but live visibly in the
judgment layer rather than passing as spec. **Rejected:** judged-tier
requirements (blended confidence); banning judged content entirely
(ineffable commitments retreat to chat history and get trampled — the
original failure mode). Closes GAP-8; Verdict is now governed (CRI-R2/R3).
