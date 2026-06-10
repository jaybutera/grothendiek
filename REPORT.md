# Check report — 2026-06-10, run 4 (hand-run; no tooling exists yet)

Per CHK-R2 / D3, gaps are phrased as questions for the designer. Per CHK-I1,
every finding carries a witness or location. Per CHK-R10, Proven and Judged
are reported separately.

## Resolved since run 3

- **GAP-9 → closed by D13** (`specs/criteria.md`): Artifact = pinned,
  immutable snapshot of the implementation. Verdicts split: *execution*
  verdicts (indexed by criterion × artifact, expire when a change touches
  the footprint — CRI-R4) vs. *reconciliation* rulings (criterion ×
  criterion, artifact-independent, expire when either criterion changes —
  CRI-R5).
- **GAP-10 → closed by D14** (`specs/checking.md`): frame groups are
  Entities, not name prefixes. Vocabularies declare entities; every
  variable belongs to one; situation space factors as the product of
  entity spaces. Frames range over the entity in the glued vocabulary;
  growth emits a `frame_strengthened` finding (CHK-R11), never silent.

## Proven (mechanical findings)

**Conflicts:** none found. (CRI-R4/R5 fire on disjoint events; CRI-R2/R3
partition on `pair.ruling`.)

**Dead rules:** none found (no invariant cards exist yet).

## Judged (criterion execution status)

No criterion cards exist yet; nothing to execute.

## Gaps

**GAP-3 — requirements have no lifecycle.** (open; three runs of in-place
edits now)
Witness: CRI-R1/R2/R3 were edited in place this run.
→ *Delete, or supersede-only like decisions? Should in-place edits require
a delta at minimum?*

**GAP-4 — vocabulary evolution is ungoverned.** (open; narrowed by D14)
D14 governs vocabulary *structure* (entities, membership, growth
visibility); the *approval process* for changes is still uncovered.
Witness: this run added three event values to `criteria.md`'s vocabulary
with no governing card.
→ *Should vocabulary changes be deltas requiring designer approval?*

**GAP-5 — delta rejection is half-specified.** (open, unchanged)
Witness: situation `event = delta_rejected` — no card fires.
→ *Discard, or record with reason so agents stop re-proposing?*

**GAP-6 — nothing says when check or review runs.** (open, unchanged)
→ *check: CI gate, pre-edit hook, on-demand? work_review: every PR, every
delta, designer-initiated?*

**GAP-11 — "since the last accepted check" implies a baseline.** (new,
consequence of D14/CHK-R11)
`frame.strengthened` compares against a previous state, but check is
stateless and CHK-R7 forbids it writing anything.
Witness: CHK-R11's guard variable has no defined reference point.
→ *Does an accepted check write a lockfile (who accepts it — does this
overload delta approval?), or is the baseline simply the last committed
REPORT, making the git history the state?*

## Coverage (vs `system.md`)

Covered: Spec, Interface, Card, Requirement, Criterion, Guard, Effect,
Frame, Entity, Procedure, Footprint, Decision, Conflict, Gap, Witness,
Finding/Check report, Query, Delta, Designer, Builder agent, Invariant,
Don't-care, Verdict, Artifact, Vocabulary (structure via D14; evolution
pending GAP-4).

Uncovered: none at the concept level — every glossary entry now has at
least one governing card. Remaining exposure is process-shaped (GAP-3..6,
GAP-11), not concept-shaped.
