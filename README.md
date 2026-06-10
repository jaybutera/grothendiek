# Grothendiek

A spec system for the designer ↔ builder-agent interface. Specs are markdown
files whose prose stays primary; a small formal surface (frontmatter
vocabulary + `when/then` requirement cards) makes them **composable** and
**checkable**:

- **Conflicts** — two requirements whose guards overlap on some situation but
  demand incompatible outcomes (a pullback of guards with mismatched `then`s).
- **Gaps** — in-scope situations no requirement covers, reported as questions
  for the designer.
- **Queries** — agents pull governing requirements/decisions before editing
  (`--touching` = footprint intersects the work; `--governing` = footprint
  contains it).
- **Decisions** — first-class cards with rationale; they can be superseded
  explicitly but never overwritten silently.

This repo is self-hosted: the system's own behavior is specified in its
own format, and `spec-check` (Python, uv-managed) checks it — `uv run
spec-check .` regenerates `REPORT.md`, currently clean at zero findings.

## Foundation

The language is founded in category theory: `specs/theory.md` states the
formalization (T1–T10) and is kept honest three ways, per the system's
own checkability doctrine (D19): the decidable theorems are executable
laws (`tests/test_laws.py` — lattice, cover-partition, adjunctions);
implementation-correspondence claims are judged criteria (THY-C1..C4)
with footprints over the tool modules, so touching the code stales the
math; and the construct inventory test keeps the theory total over the
language surface. Cards never carry theory annotations — cards are
programs, the theory is about the language, and downstream corpora
inherit it by construction through the fixed grammar-in/findings-out
surface.

## Core vocabulary and composition

The primitives (full glossary in `system.md`; theory in `specs/theory.md`):

- **Vocabulary** — finite enumerations: `sub.state: [active, paused, ...]`.
  Variables group into **entities** (`sub.*`); **situation space** is the
  product of all domains, factored by entity (T2).
- **Guard** — a conjunction of `var = value` / `var != value` literals; it
  denotes an axis-aligned region of situation space, a card's domain (T3).
- **Effect** — assignments the card commits to: transitions
  (`sub.state -> paused`) and response facts (`charge = no`) (T4).
- **Cards** — requirement (guard → effects, mechanical), criterion
  (footprint + procedure, judged), decision (choice + rationale,
  supersede-only), invariant ("impossible"), dont-care ("accepted, with
  reason"), verdict (a recorded check outcome).

How things compose — each level has one composition rule and one
obstruction, and the obstruction is always a reported finding:

- **Specs compose by import.** Shared concepts go through interfaces;
  the merged vocabulary is the colimit of the import diagram (T1).
  Obstruction: `duplicate_definition` — same name, different meanings,
  no shared interface.
- **Requirements compose pointwise.** Where guards overlap, effects on
  disjoint variables both apply; same variable, same value is harmless
  redundancy. Obstruction: `conflict` — same variable, different values,
  no `overrides:` link (D9). Frames join this rule by desugaring to
  `-> unchanged` effects (D12).
- **Coverage composes globally.** A situation is covered if *any* spec's
  card covers it (D17); invariants and dont-cares remove regions
  explicitly. Obstruction: `gap` — a situation that is neither covered,
  impossible, nor accepted (D10: silence is never meaningful).
- **Work composes with the spec by query.** `--touching` (footprint
  meets the work) and `--governing` (footprint contains it) are the two
  adjoints of restriction (T6) — the only two membership semantics there
  are.

## Reflection

The checker is configured by the spec it checks (D18): finding severities
are read from `specs/checking.md`'s `severities:` block before each run —
read config → compute → emit, a well-founded chain. Findings never feed
back into the evaluation that produced them, because the closed loop
admits the liar: `when: finding.gap = none then: finding.gap = emitted`
has no consistent assignment (negation + unstratified self-application —
Tarski's theorem in a when-clause; the same law as Datalog's stratified
negation).

**Possible future — stratified reflection:** if specs ever need to talk
about checker outputs at their own level, the safe extension is vocabulary
*levels*: level-n+1 guards may mention only level-≤n variables, enforced
as a cycle check on the variable dependency graph. That is Tarski's
hierarchy of metalanguages as a language feature. Until a second genuinely
reflective spec exists, this stays a note, not a mechanism.

## Layout

```
system.md              glossary: the coverage target
specs/interfaces/      shared vocabulary (interfaces other specs import)
specs/*.md             behavior specs (requirement + decision cards)
specs/theory.md        the categorical foundation (T1–T10, THY criteria, D19)
src/spec_check/        the checker (parser, region algebra, checker, report)
tests/                 unit + fixture + law + inventory tests (pytest)
prompts/               implementation prompts for builder agents
REPORT.md              latest check output (tool-generated, committed per PRO-R1)
```

## Card format

```
## XXX-R1: short name                      ← requirement
when: <guard over vocabulary terms>
then: <effects: assignments to vocabulary variables>
because: [[D2]]                            ← rationale links

## D2 (decision, YYYY-MM-DD): short name   ← decision
<choice, rejected alternatives, and why>   supersedes: D1
```

Every card declares how it is checked (D7→D11): **requirements** are fully
mechanical — guard + effects in vocabulary terms, checked by enumeration,
with an optional `frame:` clause freezing an entity's remaining
attributes (D12, D14);
**criteria** are the structurally separate judged layer — footprint + an
evaluation procedure an agent executes at review time, verdicts recorded
as judgment calls. Criteria never count toward coverage and never enter
check-time conflict analysis (`specs/criteria.md`). A card with no check
procedure cannot exist. Situations escape gap detection only via explicit
`invariant:` or `dont-care:` cards — silence is never meaningful (D10).
