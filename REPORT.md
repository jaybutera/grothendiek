# Check report — 2026-06-10, run 5 (hand-run; no tooling exists yet)

Per CHK-R2 / D3, gaps are phrased as questions for the designer. Per CHK-I1,
every finding carries a witness or location. Per CHK-R10, Proven and Judged
are reported separately. Per PRO-R1, this report lands in the same commit
as the delta that produced it.

## Resolved since run 4

- **GAP-11 + GAP-6 → closed by D15** (`specs/process.md`, new): git is the
  memory, the commit is the clock. Check runs before every spec commit and
  on demand (PRO-R2); review runs per artifact PR (PRO-R3); the committed
  REPORT at HEAD is the baseline for CHK-R11; "accepted check" = "commit".
- **GAP-3 + GAP-4 + GAP-5 → closed by D16** (`specs/authoring.md`): the
  delta is the only write path for any spec change, by any agent (AUT-R7).
  Requirements are current-commitment-valued — editable/deletable by
  approved delta, lineage kept by git; decisions stay supersede-only.
  Rejected deltas are retained with reasons and surfaced by pre-edit
  queries (AUT-R8), ending the re-proposal loop.

## Proven (mechanical findings)

**Conflicts:** none found. (PRO-R1/R2 share guard `event = spec_commit`
but write disjoint variables — `report.fresh` vs. `check.executed` — and
compose per D9.)

**Dead rules:** none found (no invariant cards exist yet).

## Judged (criterion execution status)

No criterion cards exist yet; nothing to execute.

## Gaps

**GAP-12 — the spec↔implementation correspondence is undeclared.** (new,
and now the only open gap)
CRI-R4 branches on `diff.touches_footprint` and PRO-R3 reviews artifact
changes — both presume a mapping from implementation regions (files,
modules, endpoints) to spec footprints, and no card defines it.
Witness: any code diff — nothing currently determines which criteria or
requirements it touches, so AUT-R4's pre-edit query and CRI-R4's
staleness rule cannot actually be computed against code.
→ *How is the correspondence declared — footprint annotations naming code
paths on cards, a separate mapping file owned like a spec, or inferred by
an agent at review time and recorded as it goes?*

## Coverage (vs `system.md`)

Covered: every glossary concept. Process gaps GAP-3..6 and GAP-11 are
closed; the spec is, at its current vocabulary, conflict-free and
complete except for GAP-12.

## Note

For the first time the gap list does not point inward at the spec
system's own mechanics — it points outward, at the seam between the spec
and a real codebase. The natural next delta is not more spec: it is the
first implementation step (`spec check` as a tool, run against this
repo), which is also exactly the work that will force GAP-12's answer.
