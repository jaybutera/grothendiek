# Build `spec check` — v1 implementation prompt

## Context

This repo (`cat-spec`) is a self-hosted spec system for the designer ↔
builder-agent interface. Markdown spec files carry a small formal surface:
YAML frontmatter (vocabulary, imports) plus "cards" — requirements
(guard → effects over enumerated variables), decisions, invariants,
don't-cares. The system's own behavior is specified in its own format.

Read these before writing any code, in this order: `README.md`,
`system.md`, `specs/interfaces/core.md`, `specs/checking.md`,
`specs/criteria.md`, `specs/authoring.md`, `specs/process.md`,
`specs/querying.md`, and `REPORT.md` (run 5 — the latest hand-run check,
your reference output). The specs in `specs/` are simultaneously your
requirements document and your primary test input. Decision cards
(D1–D16) carry binding rationale; if an implementation choice contradicts
a decision card, the decision wins.

## Mission

Implement the `spec check` CLI in Python, managed with uv, that
mechanizes the checking spec (`specs/checking.md`) and replaces the
hand-run REPORT.md. Acceptance:

1. `uv run spec-check .` runs on this repo and produces a report in the
   REPORT.md style: Proven and Judged sections walled off (CHK-R10),
   every finding carrying a witness or file/card location (CHK-I1), gaps
   phrased as plain-English questions (D3).
2. The full test suite passes via `uv run pytest`, including fixture
   specs that each provoke every finding kind at least once.
3. Your final summary lists any discrepancies between your tool's output
   on this repo and REPORT.md run 5, with your analysis of which is
   right (the hand-run report may contain errors — finding them is a
   feature, not a failure).

## Hard constraints

- **Never modify anything in `specs/`, `system.md`, or the decision
  cards.** Check is read-only (CHK-R7), and all spec changes go through
  designer-approved deltas (AUT-R7). The existing cards were hand-written
  and some will not conform to the grammar below — that is expected and
  is dogfood value. Emit a `nonconforming_card` finding for each, and
  list **proposed deltas** (exact suggested card text) in your final
  summary for the designer to approve. Do not "fix" them yourself.
- **No silent coverage caps.** Wherever you bound work (region
  clustering, enumeration limits), say so in the report output.
- You MAY regenerate `REPORT.md` via the tool (that is the milestone) —
  note in your summary that it replaces the hand-run report.

## Format and grammar to implement

### Frontmatter (YAML between `---` fences)

- `spec: <name>`, optional `kind: interface`
- `imports:` list of `{from: <spec>, use: [names]}` and/or
  `{from: <spec>, rename: {Their: Ours}}`
- `vocabulary:` map of `<variable>: [value, ...]` (finite enumerations).
  Variables are dotted: `sub.state`, `user.state`, or bare: `event`.
- `entities:` optional map `<entity>: [variable, ...]`. Per D14 entities
  should be declared; current files don't declare them. Interim rule:
  derive the entity from the dotted prefix (`sub.state` → entity `sub`),
  and emit a warning finding proposing an explicit `entities:` block.
- Interface files use `defines: {concepts, relations, values}` — parse
  for import resolution and duplicate-definition checking; their
  relations/values need no deeper semantics in v1.

### Cards (markdown `##` sections)

- Requirement: `## <PREFIX>-R<n>: <title>` with fields on following
  lines: `when:`, `then:`, optional `frame:`, `overrides:`, `because:`.
  Fields continue across indented lines.
- Invariant: `## <ID> (invariant): <title>` with an `invariant:` line.
- Decision: `## D<n> (decision, <date>): <title>`, free prose; parse
  `supersedes: D<m>` and `status: superseded by [[D<m>]]` lines.
- `because: [[D7]], [[D9]]` — link syntax, used for stale-ref checking.

### Guard grammar (`when:`)

```
guard  := clause ( "and" clause )*
clause := variable ("=" | "!=") value
```

No `or`, no parens in v1 — a guard denotes a conjunction of literals,
i.e. an axis-aligned region (a "cube") of situation space. Unparseable
guards → `nonconforming_card` finding (with the unparseable fragment
quoted), card excluded from semantic analysis, exclusion noted in report.

### Effects grammar (`then:`)

```
effects    := assignment ( "," assignment )* [ "—" annotation-prose ]
assignment := variable "->" value      # state transition
            | variable "=" value       # response fact
```

Parse the leading comma-separated assignments; an em-dash (`—`) ends the
formal part, the rest is annotation prose. A `then:` with no parseable
leading assignment is nonconforming.

### Frame desugaring (D12 + D14)

`frame: <entity>` expands, before any analysis, to `var -> unchanged`
for every variable of that entity not already assigned in `then:`.
`unchanged` is a reserved value that clashes with any concrete
assignment to the same variable (and is compatible with itself).

## Checking semantics (the actual algorithms)

Vocabulary merging: union across all spec files after import/rename
resolution. The same variable declared with different value sets in two
files → `duplicate_definition` error naming both.

- **unknown_term** (CHK-R3): any variable or value in a guard, effect,
  frame, or invariant that is not in the merged vocabulary. Error.
- **duplicate_definition** (CHK-R4): a concept defined (via `defines:`)
  in two specs neither of which imports it from a common interface. Error.
- **conflict** (CHK-R1, D9): for each pair of requirement cards after
  frame desugaring — guards overlap (their conjunctions are jointly
  satisfiable: no variable forced to two different values), AND some
  variable is assigned different values by the two `then:`s, AND no
  `overrides:` link connects the pair in either direction. Error. Witness:
  one concrete satisfying assignment of the overlap, rendered in English.
- **gap** (CHK-R2, D10): a situation covered by no requirement guard and
  excluded by no invariant/don't-care card. Enumerate over the *relevant
  projection*: for each spec file, the product of the variables its own
  cards constrain (the full cross-spec product explodes and asks nothing
  useful). Cluster uncovered situations into maximal cubes and emit ONE
  question per cube, phrased per D3: "What should happen when
  event = renewal_due and sub.state = paused (any user.state)?" State the
  projection rule in the report header — bounded coverage must be loud.
- **dead_rule** (CHK-R8): a requirement whose desugared guard region is
  entirely contained in the union of invariant-excluded regions. Error.
- **stale_decision_ref** (CHK-R5): a `because:` link to a decision whose
  card carries `status: superseded by`. Warning, naming the superseding
  decision.
- **orphan_spec**: a spec that imports nothing and is imported by
  nothing. Warning.
- **frame_strengthened** (CHK-R11, D15) — stretch goal: baseline = parse
  `git show HEAD:REPORT.md` for a machine-readable entity-attribute
  snapshot you embed in your report output (e.g. an HTML comment block).
  If no baseline exists, print "baseline unavailable — first tool run"
  and skip. Do not invent a lockfile (D15 explicitly rejects one).
- **Judged section** (CHK-R10): list criterion cards found (there are
  currently none) with "no execution data — review-time execution is out
  of scope for spec check." Never blend this section with Proven.

Severity → exit code: errors (conflict, unknown_term,
duplicate_definition, dead_rule) → exit 1; warnings only (gap,
stale_decision_ref, orphan_spec, nonconforming_card, frame_strengthened)
→ exit 0; `--strict` promotes warnings to errors.

## Out of scope for v1

- `spec query` (--touching/--governing) — design the internal model so
  footprint-vs-region pullbacks are easy to add, but don't build the CLI.
- Criteria execution, verdicts, deltas, the work_review flow.
- The spec↔code correspondence (GAP-12 in REPORT.md) — do not attempt it.

## Engineering requirements

- Python ≥ 3.12, uv-managed: `pyproject.toml` with
  `[project.scripts] spec-check = ...`, `uv run spec-check`, `uv run
  pytest` both working from a fresh clone.
- Dependencies: PyYAML only at runtime (frontmatter is plain YAML between
  `---` fences — split it yourself, no frontmatter libs). pytest as the
  dev dependency. Standard library for everything else, including CLI
  (argparse) and output. No rich, no click, no pydantic.
- Fully type-annotated; dataclasses for the model (Spec, Card, Guard,
  Effect, Finding, ...). Keep the guard/region algebra (cube overlap,
  containment, subtraction for gap clustering) in its own module with
  direct unit tests — it is the mathematical core and the most likely
  place for bugs.
- CLI: `spec-check [PATH] [--strict] [--json] [--output FILE]`. `--json`
  emits findings as structured JSON; default output is the markdown
  report.
- Tests: unit tests for parser, cube algebra, frame desugaring, conflict
  and gap semantics; fixture spec directories under `tests/fixtures/`,
  including one reproducing the billing/dunning conflict (a suspended
  user with payment retries — R1 "charge = no" vs R9 "charge = yes",
  witness expected) and one with an invariant that kills a rule
  (dead_rule). A golden test runs the tool on the repo root and asserts
  the finding set (not exact prose).

## Final summary must include

1. Findings the tool produced on this repo, vs. REPORT.md run 5 — what
   matches, what differs, and which you believe is correct.
2. The nonconforming-card list with exact proposed delta text for the
   designer (do not apply them).
3. Anything in `specs/checking.md` you could not implement as specified,
   stated plainly — these become gap material for the next delta cycle,
   so vagueness here is a bug.
