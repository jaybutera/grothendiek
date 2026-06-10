---
spec: theory
imports:
  - from: core
    use: [Spec, Requirement, Criterion, Guard, Effect, Entity, Footprint,
          Verdict, Artifact, Finding]
---

# Theory

The categorical foundation of the spec language. **Scope: the language and
its checker, not any corpus.** Cards are programs; this document is about
the language — downstream projects inherit these properties by
construction, through the fixed surface of grammar-in, findings-out, the
way every well-typed program inherits type soundness from its compiler
without per-program proof. No card here or elsewhere carries a theory
annotation; the statements below are quantified over *all possible
corpora*.

Each numbered statement lists the language constructs it founds
(machine-checked for totality by `tests/test_theory_inventory.py`) and is
pinned by the law tests in `tests/test_laws.py` where finitely decidable,
and by the THY criteria below where it is a correspondence claim about
the implementation.

## T1 — corpora and the colimit
Constructs: `spec`, `interface`, `imports`, `vocabulary`,
`duplicate_definition`, `orphan_spec` (an isolated object in the diagram).
A corpus is a finite diagram of specs and interfaces; imports (with
renamings) are the morphisms. The merged vocabulary is the colimit of the
diagram: shared concepts are identified along interfaces, and a variable
declared with different value sets in two specs with no common apex is a
failure of the colimit to exist as declared — reported, not repaired
(`merge_vocabulary`).

## T2 — situation space and entities
Constructs: `situation`, `variable`, `entity`, `entities_underspecified`,
`unknown_term` (a term that resolves in no factor of the glued vocabulary).
Situation space S is the product of the (finite) variable domains of the
glued vocabulary. Entities are a chosen factorization S ≅ ∏ₑ Sₑ (D14);
every variable belongs to exactly one factor. Cartesian, finite, discrete:
every later operation is finite set algebra, which is why the theorems in
this file are decidable.

## T3 — guards as subobjects
Constructs: `guard`, `requirement`, `when`, `nonconforming_card` (text
that denotes no subobject is excluded from semantics, loudly).
A guard is a conjunction of literals over declared variables; it denotes
an axis-aligned cube — a subobject of S. The cubes form a meet-semilattice
with relative complements (`intersect`, `subtract`); `subtract_region`
computes complements as finite disjoint unions of cubes. A requirement is
a function fragment: its guard is its domain.

## T4 — effects as sections, conflict as gluing failure
Constructs: `effect`, `then`, `conflict`, `overrides`, `frame`, `unchanged`,
`dead_rule`.
Effects are partial assignments — sections over the variables they write.
Two requirements compose where their sections agree on the overlap of
their write-sets; a conflict (D9) is precisely a gluing failure: guards
overlap and sections disagree at a shared variable, with no declared
`overrides:` morphism resolving the pair. A frame (D12/D14) is the
identity on its entity factor away from the written coordinates,
desugared to explicit `-> unchanged` sections so D9 needs no new rule. A
dead rule (CHK-R8) is a guard-subobject contained in the union of
impossible regions.

## T5 — coverage as a cover
Constructs: `gap`, `invariant`, `dont-care`, `coverage`.
The cards' guard-subobjects, the invariant-excluded regions, and the
dont-care regions must jointly cover S (D10): every situation is covered,
impossible, or accepted — silence is never meaningful. A gap is the
obstruction: a nonempty complement, returned as disjoint witness cubes
(`coverage_complement_cubes`). Coverage is computed against the glued
corpus (D17): a local section from any spec covers globally — the
local-to-global step.

## T6 — queries as the adjoint triple
Constructs: `touching`, `governing`, `footprint`, `query`.
For a work region U ↪ S, restriction of the spec along U has adjoints on
both sides: touching is the existential image (footprint ∩ U ≠ ∅, the
left adjoint), governing is the universal image (footprint ⊇ U, the
right). ∃ ⊣ restriction ⊣ ∀ (D4): there are exactly two membership
semantics, which is a theorem, not an API choice.

## T7 — projection
Constructs: `projection`, `gap clustering`.
Reporting projects S onto the variables a spec's own guards constrain.
Existential projection π∃ is left adjoint to cylindrification π*:
π∃(A) ⊆ B ⟺ A ⊆ π*(B). D17's shared-variable rule is the guard against
vacuous covering: a cube constraining no projection variable has
π∃(cube) = ⊤, so it is excluded from contributing rather than allowed to
cover everything trivially.

## T8 — artifacts and verdict transport
Constructs: `criterion`, `verdict`, `artifact`, `work_review`, `procedure`.
Artifacts (pinned commits) form a category with ancestry arrows. An
execution verdict lives over a (criterion version, artifact) pair and
transports along exactly the arrows whose diff misses the criterion's
footprint (CRI-R4/R6) — restriction along footprint-disjoint maps is
free; anything else stales. Reconciliation rulings live over criterion
pairs and never reference artifacts (D13).

## T9 — reflection, stratified
Constructs: `severities`, `finding`, `unstratified_guard`,
`unclassified_finding_kind`, `config`.
The checker is configured by the corpus (D18) in a well-founded chain:
corpus text → derived analysis facts → findings. The stratification law:
**a requirement guard may mention input and analysis variables, never
finding variables** — findings are write-only at their own level.
Violating it admits the liar (`when: finding.gap = none then: finding.gap
= emitted`, no consistent assignment — Tarski's undefinability in a
when-clause; operationally, Datalog's stratified-negation law). The
checker enforces this as the `unstratified_guard` finding (CHK-R13).
Invariant and dont-care cards are exempt: they are claims about outputs,
not rules fired by reading them. Possible future leveling is recorded in
README.md.

## T10 — process: git as the state category
Constructs: `spec_commit`, `baseline`, `frame_strengthened`, `delta`,
`decision`, `stale_decision_ref` (supersession is the only morphism between
decision versions; a reference into a superseded one is flagged).
The repo's commits are the system's state; the committed REPORT at HEAD
is the baseline along which stateful comparisons (CHK-R11) are made
(D15). A spec commit is itself an artifact in the T8 sense — the spec's
own world, pinned.

## The anchor
The tower does not certify itself: the law tests are run by pytest, not
by spec-check, and faithfulness of implementation to theory is judged
(THY criteria), not enumerated. The chain of trust terminates where the
spec already says it does — AUT-DC2, the designer as root of trust — and
the founding act is recorded as [[D19]] below. The system verifies
everything except the act of trusting the verifier, and names that act.

---

## THY-C1: coverage implements the cover
footprint: [src/spec_check/checker.py (check_gaps, _project_cube),
            src/spec_check/region.py (coverage_complement_cubes), T5, T7]
procedure: verify, statement by statement against T5/T7, that check_gaps
  computes the complement of the corpus-global cover within each
  projection: covered ⊔ excluded ⊔ uncovered partitions the projection
  top; covering cubes are existentially projected onto shared variables;
  subject-disjoint cubes contribute nothing. Agent-executed when the
  footprint changes.

## THY-C2: the region algebra is the subobject lattice
footprint: [src/spec_check/region.py, T3, T6]
procedure: verify that intersect/subtract/cube_subset implement meet,
  relative complement, and ≤ of the cube sublattice of Sub(S), and that
  touching/governing membership match the ∃/∀ images of T6. The law
  tests pin the equations; this criterion verifies the *reading* — that
  the code's operations are these operations and not approximations.

## THY-C3: reflection stays well-founded
footprint: [src/spec_check/run.py (_apply_spec_severities, lint),
            specs/checking.md (severities, CHK-R12, CHK-R13), T9]
procedure: verify the chain corpus → analysis → findings is acyclic in
  the implementation: severities are read before findings are classified;
  no guard evaluation consults the current run's findings; the
  unstratified_guard lint scans every requirement guard against the
  finding entity. Agent-executed when run.py or checking.md changes.

## THY-C4: vocabulary merge is the colimit
footprint: [src/spec_check/checker.py (merge_vocabulary), specs/interfaces/core.md, T1]
procedure: verify that merged vocabulary identifies shared declarations
  along interfaces and reports same-name/different-values clashes as
  duplicate_definition rather than silently unioning semantics. T1 is the
  statement; the criterion confirms the code's merge is that pushout and
  nothing more creative.

---

## D19 (decision, 2026-06-10): the foundation is ratified
The designer accepts this document, the law tests, and the THY criteria
as the founding of the spec language in category theory, at the commit
that introduces them. Standing rule: a change touching any THY
footprint must keep `tests/test_laws.py` green and re-verify the stale
THY criteria before merge; the construct inventory test keeps this
document total over the language's surface. Downstream corpora inherit
the foundation by construction and cannot affect it through any card.
**Rejected:** per-card theory annotations (level error — cards are
programs, the theory is about the language; bureaucratizes every future
project for zero proof value); mechanized proof as a gate (Lean
mechanization remains the named upper bound, adopted only if the tool's
ambitions outgrow tests-plus-judged-criteria).
