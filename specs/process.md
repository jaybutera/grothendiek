---
spec: process
imports:
  - from: core
    use: [Spec, Artifact, Finding, Delta]
vocabulary:
  event: [spec_commit, artifact_pr]
  report.fresh: [yes, no]      # REPORT regenerated as part of this commit
  check.executed: [yes, no]
---

# Process

When things run, and where state lives. The answer to both is git: the
spec repo's history *is* the system's memory ([[D15]]). Check stays pure
(CHK-R7) — it computes; authoring commits what it computed.

## PRO-R1: every spec commit carries a fresh report
when: event = spec_commit
then: report.fresh = yes — the delta and the REPORT it produces land in
      the same commit. The committed REPORT at HEAD is the baseline for
      stateful comparisons (CHK-R11's frame.strengthened); "accepted
      check" and "commit" are the same event
because: [[D15]]

## PRO-R2: check runs before every spec commit, and on demand
when: event = spec_commit
then: check.executed = yes — a spec commit with findings unexamined by
      the designer cannot land; on-demand runs are always available and
      write nothing (CHK-R7)
because: [[D15]]

## PRO-R3: review runs per artifact change
when: event = artifact_pr
then: work_review executes (CRI-R1) with the change's head commit as the
      Artifact; execution verdicts index against it
because: [[D13]], [[D15]]

---

## D15 (decision, 2026-06-10): git is the memory, the commit is the clock
No lockfile, no database, no second source of truth: the spec repo's git
history is the system's state. The baseline for "since the last accepted
check" is the committed REPORT at HEAD; acceptance is the commit itself;
prior versions of every card are retrievable from history. This also
makes the spec repo self-similar with D13: a spec commit is an Artifact —
the spec's own world, pinned. **Rejected:** a lockfile written by check
(violates CHK-R7 and invents a designer-invisible acceptance step); a
state database (duplicates what git already does immutably and
addressably). Closes GAP-11 and the cadence half of GAP-6.
