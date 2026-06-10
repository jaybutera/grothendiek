# System glossary

The coverage target: every concept here should be defined by some interface
and have its behavior governed by at least one requirement card. `spec
coverage` (future) diffs this list against the union of spec footprints.

- **Spec** — a markdown file: frontmatter signature + prose body + cards.
- **Interface** — a deliberately small spec that exists to be imported, so
  shared concepts are provably the same concept.
- **Vocabulary** — finite enumerations of states/events; the coordinate
  system for situation space. Variables are grouped into entities.
- **Entity** — a declared group of variables (User, Subscription, …); a
  factor of situation space; the range of a frame clause.
- **Artifact** — a pinned, immutable, addressable snapshot of the
  implementation (a commit hash); what judged procedures execute against.
- **Situation** — one assignment of values to vocabulary terms.
- **Card** — the atomic, addressable unit of spec content: requirement,
  decision, invariant, don't-care, or verdict.
- **Requirement** — a fully mechanical commitment: guard → effects, checked
  by enumeration.
- **Criterion** — a review obligation in the judged layer: footprint +
  procedure, executed by an agent at review time; never counts toward
  coverage, never enters check-time conflict analysis.
- **Guard** — predicate over situations, written in vocabulary terms; the
  card's domain.
- **Effect** — an assignment to a vocabulary variable (a transition like
  `sub.state -> paused`, or a response fact like `charge = no`).
- **Frame** — an optional clause naming an entity whose attributes are
  frozen unless mentioned; desugars to `-> unchanged` effects.
- **Procedure** — a criterion's declared evaluation steps, executed by an
  agent; verdicts are judgment calls.
- **Invariant** — a card claiming a region of situation space is impossible;
  falsifiable, and a verification obligation against the implementation.
- **Don't-care** — a card accepting any behavior in a possible region, with
  rationale.
- **Verdict** — execution kind: a procedure's outcome at one (criterion,
  artifact) pair; reconciliation kind: a designer ruling on contradictory
  criteria, artifact-independent.
- **Footprint** — the region of situation space (or topic set) a card governs.
- **Decision** — a recorded choice with rationale and supersession links.
- **Conflict** — overlapping guards with incompatible outcomes.
- **Gap** — an in-scope situation covered by no guard.
- **Witness** — a concrete situation demonstrating a conflict or gap.
- **Check report** — output of `spec check`: findings, each with a witness.
- **Query** — retrieval of cards relevant to a region/topic of work.
- **Delta** — a proposed card change awaiting designer approval.
- **Designer** — the human; reads prose and answers questions; does not read code.
- **Builder agent** — an AI agent that edits the system; queries before editing.
