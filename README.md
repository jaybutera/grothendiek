# cat-spec

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
with an optional `frame:` clause freezing a variable group (D12);
**criteria** are the structurally separate judged layer — footprint + an
evaluation procedure an agent executes at review time, verdicts recorded
as judgment calls. Criteria never count toward coverage and never enter
check-time conflict analysis (`specs/criteria.md`). A card with no check
procedure cannot exist. Situations escape gap detection only via explicit
`invariant:` or `dont-care:` cards — silence is never meaningful (D10).
