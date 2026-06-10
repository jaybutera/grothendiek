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

This repo is self-hosted: the system's own behavior is specified in its own
format. No tooling exists yet — `REPORT.md` is a hand-run check.

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
REPORT.md              latest check output (currently hand-generated)
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
