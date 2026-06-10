---
spec: core
kind: interface
vocabulary:
  event: [check_run, query_run, work_review, artifact_changed,
          criterion_changed, spec_commit, artifact_pr, gap_answered,
          delta_proposed, delta_approved, delta_rejected,
          decision_change_needed, agent_edit_planned, spec_change_planned]
entities:                  # the factorization of situation space (D14)
  actor: [actor]
  annotation: [annotation.criterion_present]
  approver: [approver]
  card: [card.footprint_vs_region, card.kind, card.has_because, card.checkable]
  change: [change.packaged_as_delta]
  check: [check.executed]
  collision: [collision.with_active_decision]
  concept: [concept.multiply_defined, concept.via_shared_interface]
  config: [config.source]
  criterion: [criterion.touched]
  decision: [decision.recorded]
  decision_ref: [decision_ref.target_status]
  delta: [delta.status, delta.drafted, delta.retained]
  diff: [diff.touches_footprint]
  edit: [edit.proceeds]
  escalation: [escalation]
  event: [event]
  finding: [finding.pointer, finding.conflict, finding.gap, finding.dead_rule,
            finding.unknown_term, finding.duplicate_definition,
            finding.stale_decision_ref, finding.frame_strengthened]
  frame: [frame.strengthened]
  guard: [guard.within_impossible]
  pair: [pair.guards_overlap, pair.effects_clash, pair.override_declared,
         pair.contradictory, pair.ruling]
  procedure: [procedure.executed]
  query: [query.mode, query.run_before_edit]
  report: [report.fresh, report.sections]
  result: [result.included, result.marked, result.includes_rationale]
  ruling: [ruling.applied]
  situation: [situation.covered, situation.criterion_present,
              situation.excluded]
  spec: [spec.write_count]
  term: [term.resolved]
  verdict: [verdict.recorded, verdict.status]
  work_review: [work_review]
defines:
  concepts:
    - Spec
    - Requirement
    - Criterion
    - Decision
    - Invariant
    - DontCare
    - Verdict
    - Artifact
    - Guard
    - Effect
    - Entity
    - Variable
    - Procedure
    - Footprint
    - Witness
    - Finding
    - Delta
  relations:
    - guard: Requirement -> Guard
    - effects: Requirement -> Effect+       # assignments to vocabulary variables
    - frame: Requirement -> Entity?         # entity frozen unless mentioned (D12, D14)
    - overrides: Requirement -> Requirement*  # declared exceptions (D9)
    - footprint: Requirement -> Footprint   # = guard region
    - procedure: Criterion -> Procedure     # declared evaluation steps
    - footprint: Criterion -> Footprint     # declared topics/regions
    - belongs_to: Variable -> Entity        # every variable has an entity (D14)
    - rules_on: Verdict -> Criterion*       # reconciliation rulings (CRI-R2)
    - at: Verdict -> Artifact?              # execution verdicts: the pinned
                                            # snapshot judged (D13)
    - because: Requirement -> Decision*     # rationale links
    - supersedes: Decision -> Decision*
    - witness: Finding -> Witness?
  values:
    card.kind: [requirement, criterion, decision, invariant, dont_care, verdict]
    verdict.kind: [execution, reconciliation]
    decision.status: [active, superseded]
    finding.kind: [conflict, gap, dead_rule, frame_strengthened, unknown_term,
                   duplicate_definition, stale_decision_ref, orphan_spec,
                   nonconforming_card, entities_underspecified,
                   unclassified_finding_kind]
---

# Core interface

The shared vocabulary every behavior spec imports. Deliberately small: it
says what the objects *are* so that checking, querying, and authoring specs
can constrain what the system *does* with them, without re-punning the nouns.

A **Requirement** is the atomic unit of the spec proper — not a type, not
a data model (see [[D1]] in `specs/checking.md`). It is fully mechanical:
a guard (its domain: a region of situation space) plus structured
`effects:` — assignments to vocabulary variables, checked by enumeration.
An optional `frame:` names an Entity whose attributes are frozen unless
mentioned; it desugars to `-> unchanged` effects (see [[D12]] and [[D14]]
in `specs/checking.md`). Its footprint is exactly its guard region.

Vocabularies declare **Entities**, and every **Variable** belongs to one —
entities are the factorization of situation space ([[D14]]), shared across
specs through interfaces like any other concept. An **Artifact** is a
pinned, immutable, addressable snapshot of the implementation (a commit
hash); it is what judged procedures execute against ([[D13]] in
`specs/criteria.md`).

A **Criterion** is the judged layer (see [[D11]] in `specs/criteria.md`):
a footprint plus a declared evaluation Procedure an agent executes at
review time, with verdicts marked as judgment calls. Criteria never count
toward coverage and have no check-time conflict semantics. A card with no
check procedure — mechanical or judged — cannot exist.

**Invariant** cards claim a region of situation space is impossible;
**DontCare** cards accept any behavior in a possible region, with rationale
(see [[D10]] in `specs/checking.md`). **Verdict** cards come in two kinds
([[D13]]): *execution* verdicts record a procedure's outcome against one
(criterion version, Artifact) pair; *reconciliation* rulings record a
designer's resolution of contradictory criteria, independent of any
artifact (see CRI-R2 in `specs/criteria.md`).

A **Decision** records a choice *and its rejected alternatives and reasons*.
Decisions are immutable once recorded: the only way to change one is a new
decision with a `supersedes:` link (see `specs/authoring.md`).
