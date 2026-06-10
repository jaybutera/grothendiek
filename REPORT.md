# Check report — 2026-06-10, run 2 (hand-run; no tooling exists yet)

Per CHK-R2 / D3, gaps are phrased as questions for the designer. Per CHK-I1,
every finding carries a witness or location.

## Resolved since run 1

- **GAP-1 → closed by D9** (`specs/checking.md`): conflict = overlapping
  guards + different values on the same effect variable + no `overrides:`
  link. Effects are mandatory and structured (D7), so this is fully
  mechanical.
- **GAP-2 → closed by D10** (`specs/checking.md`): scope = full vocabulary
  product; situations escape only via explicit `invariant:` / `dont-care:`
  cards. Silence is never meaningful. Dead-rule detection added (CHK-R8).
- **D5 → superseded by D7** (`specs/authoring.md`): no card without a check;
  two tiers (mechanical, judged); prose carries rationale only. The three
  `kind: prose` cards were converted: CHK-R4 (mechanical), CHK-R6 → CHK-I1
  (invariant), QRY-R5 (mechanical, now governs judged-card marking).
- Lint from run 1 cleared: `authoring.md` no longer imports unused `Finding`.

## Conflicts

None found. (CHK-R1's and CHK-R8's guards are disjoint on `finding` effects;
QRY-R5 composes with QRY-R1–R3 — disjoint effect variables: membership vs.
marking.)

## Gaps

**GAP-3 — requirements have no lifecycle.** (open, unchanged)
Witness: `core.md` values — `decision.status` exists, `requirement.status`
does not. The D5→D7 supersession sharpened this: requirement cards were
edited in place this run, legally, because AUT-R3 covers only decisions.
→ *Can a requirement be deleted outright, or only superseded like a
decision? Should in-place edits require a delta (AUT-R1) at minimum?*

**GAP-4 — vocabulary evolution is ungoverned.** (open, unchanged)
Witness: this run renamed `card.kind` values to `card.tier` values in
`querying.md` with no governing card.
→ *Should vocabulary changes be deltas requiring designer approval?*

**GAP-5 — delta rejection is half-specified.** (open, unchanged)
Witness: situation `event = delta_rejected` — no card fires.
→ *Is a rejected delta discarded, or recorded with the reason so agents
stop re-proposing it?*

**GAP-6 — nothing says when check runs.** (open, unchanged)
Witness: glossary "Check report" has no governing requirement on cadence.
→ *CI gate, pre-edit agent hook, both, or on-demand?*

**GAP-7 — the frame assumption is implicit.** (new)
Effects mention some variables; the rest are unconstrained — that reading
makes composition work (D9), but "and nothing else changes" is currently
inexpressible.
Witness: any card — e.g. a future `sub.state -> paused` card cannot forbid
a simultaneous `sub.price` change.
→ *Add an optional `frame:` clause ("no other variables in this group
move"), or keep unmentioned-means-unconstrained as the permanent rule?*

**GAP-8 — judged-card conflicts are undetectable.** (new, consequence of D7)
CHK-R1/D9 define conflict via effect variables; judged cards have
procedures, not effects, so judged×judged and judged×mechanical overlaps
are invisible to check.
Witness: two judged cards with overlapping footprints and contradictory
procedures would pass check silently.
→ *Should overlapping judged cards be flagged for one-time designer
adjudication, recorded as Verdict cards? (Verdict exists in core.md but
nothing governs it — currently an uncovered concept.)*

## Coverage (vs `system.md`)

Covered: Spec, Interface, Card, Requirement, Guard, Effect, Procedure,
Footprint, Decision, Conflict, Gap, Witness, Finding/Check report, Query,
Delta, Designer, Builder agent, Invariant (CHK-R8, D10), Don't-care (D10).

Uncovered: **Verdict** (defined in `core.md`, governed by nothing — see
GAP-8); **Situation/Vocabulary** still pending GAP-4.
