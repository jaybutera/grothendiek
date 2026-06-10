# Check report — 2026-06-10, run 3 (hand-run; no tooling exists yet)

Per CHK-R2 / D3, gaps are phrased as questions for the designer. Per CHK-I1,
every finding carries a witness or location. Per CHK-R10, Proven and Judged
are reported separately.

## Resolved since run 2

- **GAP-7 → closed by D12** (`specs/checking.md`): unmentioned variables
  stay unconstrained (composition survives); an optional `frame: <group>`
  clause desugars to `-> unchanged` effects, so frame violations surface
  as ordinary D9 conflicts with witnesses. No new checking machinery.
- **GAP-8 → closed by D11** (`specs/criteria.md`, new): judged cards become
  **criteria** — a distinct kind (footprint + procedure), not a requirement
  tier. Criteria never cover (CHK-R9), never enter check-time conflict
  analysis, and contradictions are settled at review time as Verdict cards
  (CRI-R2/R3). D7 superseded; its no-card-without-a-check mandate carries
  forward. Verdict is now a governed concept.

## Proven (mechanical findings)

**Conflicts:** none found. (CHK-R2 and CHK-R9 overlap on uncovered
situations but write different variables — `finding` vs. `annotation` —
so they compose per D9.)

**Dead rules:** none found (no invariant cards exist yet to exclude
regions).

## Judged (criterion execution status)

No criterion cards exist yet, so nothing to execute. First candidates when
the system specs real product behavior: tone/feel commitments that
motivated the judged layer.

## Gaps

**GAP-3 — requirements have no lifecycle.** (open; pressure increasing)
Witness: runs 2 and 3 both edited requirement cards in place, legally —
AUT-R3 protects only decisions.
→ *Can a requirement be deleted outright, or only superseded? Should
in-place edits require a delta (AUT-R1) at minimum?*

**GAP-4 — vocabulary evolution is ungoverned.** (open, unchanged)
Witness: this run renamed `card.tier` → `card.kind` in `querying.md` with
no governing card.
→ *Should vocabulary changes be deltas requiring designer approval?*

**GAP-5 — delta rejection is half-specified.** (open, unchanged)
Witness: situation `event = delta_rejected` — no card fires.
→ *Is a rejected delta discarded, or recorded with the reason so agents
stop re-proposing it?*

**GAP-6 — nothing says when check runs.** (open; now two-sided)
D11 added a second trigger surface: criteria execute at `work_review`, but
nothing defines when a work_review happens either.
→ *check: CI gate, pre-edit hook, or on-demand? work_review: every PR,
every delta, or designer-initiated?*

**GAP-9 — verdict staleness is undefined.** (new, consequence of D11)
CRI-R1 binds verdicts to artifacts "so staleness is detectable," but
nothing says when a verdict expires.
Witness: a Verdict recorded against commit X; the criterion's footprint
code is rewritten in commit Y; CRI-R3 still suppresses re-raising.
→ *Does a verdict expire when the judged artifact changes, when either
criterion card changes, or only when the designer revokes it?*

**GAP-10 — frame groups are undefined.** (new, consequence of D12)
D12 says `frame: <group>` freezes "every variable in the group," but
vocabulary declares flat variables; no card defines what a group is.
Witness: `frame: sub.*` — is `sub.*` all declared `sub.`-prefixed
variables across all specs, or only those in the card's own spec?
→ *Are groups just name prefixes resolved across the whole colimit, or
declared explicitly in vocabulary blocks?*

## Coverage (vs `system.md`)

Covered: Spec, Interface, Card, Requirement, Criterion, Guard, Effect,
Frame, Procedure, Footprint, Decision, Conflict, Gap, Witness,
Finding/Check report, Query, Delta, Designer, Builder agent, Invariant,
Don't-care, Verdict.

Uncovered: **Situation/Vocabulary** still pending GAP-4 (and now GAP-10).
