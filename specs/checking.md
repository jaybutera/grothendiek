---
spec: checking
imports:
  - from: core
    use: [Spec, Requirement, Guard, Decision, Finding, Witness]
severities:               # read by the checker before each run (CHK-R12/D18)
  error: [conflict, unknown_term, duplicate_definition, dead_rule,
          unclassified_finding_kind, unstratified_guard]
  warning: [gap, stale_decision_ref, orphan_spec, frame_strengthened,
            nonconforming_card, entities_underspecified]
vocabulary:
  pair.guards_overlap: [yes, no]          # ∃ situation satisfying both guards
  pair.effects_clash: [yes, no]           # same effect variable, different values
  pair.override_declared: [yes, no]       # an overrides: link connects the pair
  situation.excluded: [no, by_invariant, by_dont_care]
  situation.covered: [yes, no]            # ≥1 requirement guard applies;
                                          # criteria never cover (D11)
  situation.criterion_present: [yes, no]  # ≥1 criterion footprint touches
  guard.within_impossible: [yes, no]      # guard region ⊆ invariant-excluded zone
  concept.multiply_defined: [yes, no]
  concept.via_shared_interface: [yes, no]
  term.resolved: [yes, no]                # defined locally or via import
  decision_ref.target_status: [active, superseded]
  finding.pointer: [witness, location, none]
  frame.strengthened: [yes, no]           # framed entity gained attributes
                                          # since the baseline: the committed
                                          # REPORT at HEAD (PRO-R1)
  finding.conflict: [emitted, none]       # finding.* compose: several findings
  finding.gap: [emitted, none]            # can be emitted for one situation,
  finding.dead_rule: [emitted, none]      # so each kind is its own variable
  finding.unknown_term: [emitted, none]
  finding.duplicate_definition: [emitted, none]
  finding.stale_decision_ref: [emitted, none]
  finding.frame_strengthened: [emitted, none]
  annotation.criterion_present: [yes, no]
  report.sections: [separated, blended]
  spec.write_count: [zero, nonzero]
  config.source: [spec, builtin]
  guard.mentions_finding: [yes, no]       # a requirement guard reads a
                                          # finding.* variable (T9)
  finding.unstratified_guard: [emitted, none]
---

# Checking

`spec check` reads every spec, builds the import diagram, desugars `frame:`
clauses into `-> unchanged` effects ([[D12]]), enumerates situation space,
and emits findings. It is the "compiler": its errors are conflicts and
structural breakage; its warnings are gaps and staleness. It analyzes
requirements only — criteria are executed at review time, not check time
([[D11]] in `specs/criteria.md`).

## CHK-R1: conflicts are reported with witnesses
when: event = check_run and pair.guards_overlap = yes and
      pair.effects_clash = yes and pair.override_declared = no
then: finding.conflict = emitted — naming both cards, their specs, any
      `because:`-linked decisions, and at least one witness situation
because: [[D3]], [[D9]]

## CHK-R2: gaps are reported as designer questions
when: event = check_run and situation.covered = no and situation.excluded = no
then: finding.gap = emitted — containing a witness situation rendered as a
      plain-English question the designer can answer in conversation
because: [[D3]], [[D10]]

## CHK-R3: unresolved terms are errors
when: event = check_run and term.resolved = no
then: finding.unknown_term = emitted — pointing at the card and spec
      using it

## CHK-R4: no duplicate definitions without a shared interface
when: event = check_run and concept.multiply_defined = yes and
      concept.via_shared_interface = no
then: finding.duplicate_definition = emitted — naming every defining spec

## CHK-R5: stale decision references are warnings
when: event = check_run and decision_ref.target_status = superseded
then: finding.stale_decision_ref = emitted — naming the card, the
      superseded decision, and the decision that superseded it

## CHK-I1 (invariant): no finding without a pointer
invariant: finding.pointer != none — every emitted finding carries a
witness situation or a file/card location, never a bare assertion.

## CHK-R7: check is read-only
when: event = check_run
then: spec.write_count = zero — no spec file is created, modified, or
      deleted; proposing fixes is authoring's job (see
      `specs/authoring.md`), never check's

## CHK-R8: dead rules are detected
when: event = check_run and guard.within_impossible = yes
then: finding.dead_rule = emitted — naming the card whose guard can never
      fire and the invariant card(s) that exclude its entire region
because: [[D10]]

## CHK-R9: criteria do not silence gaps
when: event = check_run and situation.covered = no and
      situation.excluded = no and situation.criterion_present = yes
then: annotation.criterion_present = yes — the gap finding (CHK-R2) still
      fires; it additionally names the touching criteria, so the designer
      sees "judged attention exists here, mechanical coverage does not"
because: [[D11]]

## CHK-R10: the report never blends confidence levels
when: event = check_run
then: report.sections = separated — mechanical findings (Proven) and
      criterion execution status (Judged) are walled off; no single
      blended status is emitted
because: [[D11]]

## CHK-R13: guards never read findings
when: event = check_run and guard.mentions_finding = yes
then: finding.unstratified_guard = emitted — naming the card whose guard
      mentions a finding variable. Findings are write-only at their own
      level (the stratification law, T9 in `specs/theory.md`): a rule
      whose firing depends on the findings of the run that fires it
      admits the liar. Invariant and dont-care cards are exempt — they
      are claims about outputs, not rules fired by reading them
because: [[D18]]

## CHK-R12: the checker is configured by the spec it checks
when: event = check_run
then: config.source = spec — finding severities are read from this spec's
      `severities:` block before the run begins; a finding kind the block
      does not classify is reported as an error (the one severity the
      config cannot govern), never silently guessed
because: [[D18]]

## CHK-R11: frame growth is surfaced, never silent
when: event = check_run and frame.strengthened = yes
then: finding.frame_strengthened = emitted — naming the framed card, the
      entity, and the newly frozen attribute(s), phrased as a question:
      "R1's frame now also freezes sub.notes — intended?"
because: [[D14]]

---

## D1 (decision, 2026-06-10): requirements are the atomic unit
Cards capture functional commitments (guard → outcome), not data models.
**Rejected:** concept/type-first specs — code and SQL already own the nouns;
what code cannot hold is intent, and what agents trample is commitments.

## D2 (decision, 2026-06-10): enumeration before solvers
Vocabularies are finite enumerations, so overlap/coverage checks run by
exhaustive enumeration of situation space — plain set intersection, no
SMT dependency. **Rejected (for now):** Z3/Alloy backend — adopt only if a
real spec's situation space outgrows enumeration. Revisit then, by
superseding this decision.

## D3 (decision, 2026-06-10): error messages are interview questions
Check output is addressed to the designer, in English, with concrete
scenarios — a gap is "what should happen when …?", not "coverage 87%".
This is how an incomplete spec gets completed by a designer who will never
audit it: the system asks the next question. **Rejected:** metrics-style
reports; they inform but do not elicit.

## D9 (decision, 2026-06-10): conflict = write-write on a shared effect variable
Overlapping guards alone are not conflict — effects on disjoint variables
compose (both happen). Conflict is precisely: guards overlap on some
situation and effects assign different values to the same variable there,
with no declared `overrides:` link. Exceptions are legal only when written:
an `overrides:` link resolves the overlap (the overriding card wins).
Precedence is never inferred from guard specificity — implicit priority is
exactly the kind of unstated decision agents trample. **Rejected:** flagging
every differing-outcome overlap (drowns real conflicts in compatible ones);
specificity-based priority (implicit, untrackable). Closes GAP-1.

## D10 (decision, 2026-06-10): silence is never meaningful
Scope for gap detection = the full vocabulary product. A situation escapes
gap reporting only via an explicit card: an `invariant:` (claims the
situation is impossible — falsifiable, and a standing verification
obligation against the implementation) or a `dont-care:` (possible,
any behavior accepted, rationale required). Every other uncovered situation
is a gap. Corollary: a requirement whose guard lies entirely inside the
invariant-excluded zone is dead (CHK-R8). **Rejected:** per-spec declared
scope — silence becomes ambiguous and unchecked regions hide; bare full
product — impossible-situation questions are noise that trains the designer
to ignore the checker. Closes GAP-2.

## D12 (decision, 2026-06-10): unmentioned means unconstrained; frame: buys stasis
The default reading of effects stays *unmentioned = unconstrained* — a card
promises nothing about variables it doesn't list, which is what lets
overlapping cards compose (D9). When the designer means "and nothing else
moves," the card says so with an optional `frame: <group>` clause, which
desugars to explicit `-> unchanged` effects for every variable in the
group not already mentioned. No new checking machinery: after desugaring,
D9's write-write rule detects frame violations as ordinary conflicts with
witnesses — converting silent cross-spec disagreements ("can suspension
move prices?") into checkable ones. **Rejected:** unmentioned = unchanged
as the default (kills composition; nearly every overlap would conflict);
no frame construct at all (stasis intent stays inexpressible — an
implementation that pauses the sub *and* upgrades the plan would satisfy
the card). Closes GAP-7.

## D17 (decision, 2026-06-10): coverage is a property of the glued spec
A situation is covered if *any* card in the whole corpus covers it —
coverage is computed against the colimit, not per file; the spec that
governs an event need not be the spec whose projection asks about it.
Reporting still runs per-spec projection (the build prompt's bound on
D10's full product), with two honest rules: a card contributes to a
projection only if its guard shares at least one variable with it (a
guard about widgets cannot "cover" questions about users), and its cube
is projected existentially onto the shared variables. Finer distinctions
surface in the projection that owns the distinguishing variable.
**Rejected:** per-spec-only coverage (every spec gets asked about every
other spec's events — 16 noise gaps in run 6); unrestricted existential
coverage (a card sharing no subject with a projection would cover all of
it vacuously).

## D18 (decision, 2026-06-10): reflection is well-founded or absent
The checker reads its configuration (finding severities, CHK-R12) from
the spec corpus *before* a run; findings never feed back into the
evaluation that produced them. This is the productive, Nix-shaped form of
self-reference: read config → compute → emit, a well-founded chain. The
closed loop is deliberately rejected: if cards' guards could read the
checker's findings about the corpus containing those cards, the language
admits the liar — `when: finding.gap = none then: finding.gap = emitted`
has no consistent assignment (negation + unstratified self-application;
Tarski's theorem in a when-clause, the same law as Datalog's stratified
negation). If richer reflection is ever needed, the path is
stratification — vocabulary levels, where level-n+1 guards may mention
only level-≤n variables — recorded as possible future work in README.md.
**Rejected:** unstratified closed-loop reflection (inconsistent);
hardcoded config (tool and spec drift silently — the checker emitted two
finding kinds the spec never declared before this decision).

## D14 (decision, 2026-06-10): entities are the factorization of situation space
A frame group is not a name-prefix — it is an **Entity**. Vocabularies
declare entities; every variable belongs to one; situation space factors
as the product of entity spaces (UserSpace × SubSpace × …). `frame: sub`
means: identity on the Sub factor except at explicitly written
coordinates. A frame ranges over the entity's attributes *in the glued,
whole-system vocabulary* — entities are shared through interfaces like any
concept, so "nothing about the subscription changes" tracks the entity,
not one file's snapshot of it. Growth is visible, never silent: a new
spec adding an attribute to a shared entity strengthens existing frames
and emits a `frame_strengthened` finding (CHK-R11) for the designer to
confirm. The nouns thus re-enter the system in their correct role — not
as spec content (rejected at D1), but as the coordinate structure of the
behavioral space. **Rejected:** prefix-matching (`sub.*`) — a frame's
meaning becomes an accident of spelling, and any spec anywhere silently
strengthens every frame that shares the prefix. Closes GAP-10; Vocabulary
structure is now governed (its evolution remains GAP-4).
