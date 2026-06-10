---
spec: criteria
imports:
  - from: core
    use: [Criterion, Procedure, Verdict, Artifact, Footprint]
vocabulary:
  criterion.touched: [yes, no]      # work region ∩ criterion footprint ≠ ∅
  pair.contradictory: [yes, no]     # two touched criteria pull opposite ways
  pair.ruling: [none, valid, expired]
  diff.touches_footprint: [yes, no] # artifact change intersects the footprint
  procedure.executed: [yes, no]
  verdict.recorded: [none, execution, reconciliation]
  verdict.status: [fresh, stale]
  escalation: [none, designer]
  ruling.applied: [yes, no]
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
then: procedure.executed = yes, verdict.recorded = execution — indexed by
      the (criterion version, Artifact) pair; a bare "pass" with no
      artifact is meaningless
because: [[D11]], [[D13]]

## CRI-R2: contradictions escalate to the designer
when: event = work_review and pair.contradictory = yes and
      pair.ruling = none
then: escalation = designer — the resolution is recorded as a
      reconciliation Verdict naming both criteria and the situation that
      exposed the tension; no artifact index, it is about the criteria
      themselves
because: [[D11]], [[D13]]

## CRI-R3: rulings are remembered while valid
when: event = work_review and pair.contradictory = yes and
      pair.ruling = valid
then: ruling.applied = yes — the recorded ruling applies; the pair is not
      re-raised to the designer
because: [[D11]]

## CRI-R4: execution verdicts expire with the artifact
when: event = artifact_changed and diff.touches_footprint = yes
then: verdict.status = stale — for that criterion's execution verdicts;
      the criterion is due re-execution at the next work_review. Changes
      not touching the footprint transport the verdict for free
because: [[D13]]

## CRI-R5: rulings expire with their criteria
when: event = criterion_changed
then: pair.ruling = expired — for every reconciliation ruling naming the
      changed criterion; the next contradiction re-escalates (CRI-R2).
      Rulings otherwise persist across artifacts; they are
      artifact-independent
because: [[D13]]

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

## D13 (decision, 2026-06-10): artifacts pin the world; verdicts split in two
An **Artifact** is a pinned, immutable, addressable snapshot of the
implementation (a commit hash). The asymmetry it formalizes: requirements
are checked against the spec itself — `spec check` needs no code — while
criteria are executed against the world, so their verdicts only mean
anything indexed by *(criterion version, artifact)*. Verdicts therefore
split: **execution verdicts** ("C3 at commit a1b2c3: pass") expire when a
change touches the criterion's footprint (CRI-R4) and transport for free
when it doesn't; **reconciliation rulings** ("when C2 and C5 clash, C5
wins") are artifact-independent mini-decisions that expire when either
criterion changes or the designer supersedes them (CRI-R5). **Rejected:**
one undifferentiated Verdict kind — its staleness rule was undefinable
because the two kinds age along different axes (the world vs. the spec).
Closes GAP-9.
