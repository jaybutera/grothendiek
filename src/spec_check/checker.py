"""The checker: mechanizes specs/checking.md.

Pipeline (matches the prose of ``specs/checking.md`` and the decision cards):

1. Parse every spec, merge vocabularies (union after import/rename), deriving
   entities from dotted prefixes and proposing explicit ``entities:`` blocks
   (D14 interim rule).
2. Validate cards against the grammar -> ``nonconforming_card`` findings;
   nonconforming requirement cards are excluded from semantic analysis.
3. Desugar ``frame:`` into ``-> unchanged`` effects (D12).
4. unknown_term, duplicate_definition, conflict, gap, dead_rule,
   stale_decision_ref, orphan_spec, frame_strengthened.

The guard / region math lives in ``region.py``. This module assembles regions
and renders findings as designer-facing English.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import region as R
from .model import (
    UNCHANGED,
    Card,
    CardKind,
    Clause,
    Effect,
    EffectKind,
    Finding,
    Guard,
    Op,
    Severity,
    Spec,
)

ERROR_KINDS = {"conflict", "unknown_term", "duplicate_definition", "dead_rule"}


@dataclass
class CheckResult:
    findings: list[Finding] = field(default_factory=list)
    specs: list[Spec] = field(default_factory=list)
    domains: dict[str, tuple[str, ...]] = field(default_factory=dict)
    entity_vars: dict[str, list[str]] = field(default_factory=dict)
    var_entity: dict[str, str] = field(default_factory=dict)
    # notes printed in the report header for transparency
    notes: list[str] = field(default_factory=list)
    # projection-rule lines for the gap section header
    projection_notes: list[str] = field(default_factory=list)
    criteria: list[Card] = field(default_factory=list)
    baseline_note: str | None = None
    excluded_cards: list[tuple[str, str]] = field(default_factory=list)


# --- vocabulary -----------------------------------------------------------


def _entity_of(variable: str) -> str:
    return variable.split(".", 1)[0]


def merge_vocabulary(
    specs: list[Spec], result: CheckResult
) -> dict[str, tuple[str, ...]]:
    """Union vocabularies across specs after import/rename resolution.

    Same variable with different value sets in two specs -> duplicate_definition
    (per the build prompt). We union the value sets so later phases still have a
    usable domain, but we report the clash.
    """
    # resolve renames: {spec_name: {their_name: our_name}}
    # vocabulary variables are not interface concepts, but rename maps may apply
    # to entity names; v1 vocab variables are used as-is.
    declared: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
    for spec in specs:
        for var, vals in spec.vocabulary.items():
            declared.setdefault(var, []).append((spec.name, vals))

    merged: dict[str, tuple[str, ...]] = {}
    for var, decls in declared.items():
        value_sets = {tuple(v for v in vals) for _s, vals in decls}
        # union of all values, preserving first-seen order
        union: list[str] = []
        for _s, vals in decls:
            for v in vals:
                if v not in union:
                    union.append(v)
        merged[var] = tuple(union)
        if len({frozenset(vs) for vs in value_sets}) > 1:
            specs_named = ", ".join(
                f"{s} = [{', '.join(vals)}]" for s, vals in decls
            )
            result.findings.append(
                Finding(
                    kind="duplicate_definition",
                    severity=Severity.ERROR,
                    message=(
                        f"Vocabulary variable '{var}' is declared with "
                        f"different value sets in multiple specs: {specs_named}. "
                        f"Merging would be ambiguous; declare it once (e.g. in "
                        f"an interface) or rename the per-spec variants."
                    ),
                    location="; ".join(sorted(s for s, _ in decls)),
                )
            )
    return merged


# --- nonconforming cards --------------------------------------------------


def check_nonconforming(specs: list[Spec], result: CheckResult) -> set[str]:
    """Emit nonconforming_card findings; return ids of excluded requirements."""
    excluded: set[str] = set()
    for spec in specs:
        for card in spec.cards:
            if card.kind == CardKind.REQUIREMENT and card.parse_errors:
                detail = "; ".join(card.parse_errors)
                result.findings.append(
                    Finding(
                        kind="nonconforming_card",
                        severity=Severity.WARNING,
                        message=(
                            f"Requirement {card.card_id} in {spec.name} does not "
                            f"parse under the v1 grammar ({detail}). Excluded "
                            f"from conflict / gap / dead-rule analysis until a "
                            f"delta brings it into grammar."
                        ),
                        location=card.location,
                    )
                )
                excluded.add(f"{spec.name}:{card.card_id}")
                result.excluded_cards.append((spec.name, card.card_id))
            elif (
                card.kind in (CardKind.INVARIANT, CardKind.DONT_CARE)
                and card.parse_errors
            ):
                detail = "; ".join(card.parse_errors)
                result.findings.append(
                    Finding(
                        kind="nonconforming_card",
                        severity=Severity.WARNING,
                        message=(
                            f"{card.kind.value} card {card.card_id} in "
                            f"{spec.name} does not parse ({detail})."
                        ),
                        location=card.location,
                    )
                )
                excluded.add(f"{spec.name}:{card.card_id}")
    return excluded


# --- entities -------------------------------------------------------------


def build_entities(
    specs: list[Spec], domains: dict[str, tuple[str, ...]], result: CheckResult
) -> None:
    entity_vars: dict[str, list[str]] = {}
    var_entity: dict[str, str] = {}
    declared_entities: dict[str, tuple[str, ...]] = {}
    for spec in specs:
        for ent, vs in spec.entities.items():
            declared_entities[ent] = vs

    for var in domains:
        ent = _entity_of(var)
        var_entity[var] = ent
        entity_vars.setdefault(ent, []).append(var)

    result.entity_vars = entity_vars
    result.var_entity = var_entity

    if not declared_entities:
        # D14 interim rule: derive from prefix, propose explicit entities block
        proposal_lines = []
        for ent in sorted(entity_vars):
            vs = ", ".join(sorted(entity_vars[ent]))
            proposal_lines.append(f"  {ent}: [{vs}]")
        result.findings.append(
            Finding(
                kind="entities_underspecified",
                severity=Severity.WARNING,
                message=(
                    "No spec declares an explicit `entities:` block; entities "
                    "were derived from dotted variable prefixes (D14 interim "
                    "rule). Proposed explicit declaration (for a designer "
                    "delta):\n  entities:\n" + "\n".join(proposal_lines)
                ),
                location="vocabulary (all specs)",
            )
        )


# --- frame desugaring (D12 / D14) -----------------------------------------


def desugar_frame(
    card: Card,
    entity_vars: dict[str, list[str]],
    domains: dict[str, tuple[str, ...]],
) -> tuple[Effect, ...]:
    """Expand frame: <entity> to var -> unchanged for unmentioned vars."""
    if not card.frame:
        return card.effects
    assigned = {e.variable for e in card.effects}
    extra: list[Effect] = []
    for var in entity_vars.get(card.frame, []):
        if var not in assigned:
            extra.append(Effect(var, EffectKind.TRANSITION, UNCHANGED))
    return tuple(card.effects) + tuple(extra)


# --- guard -> cube --------------------------------------------------------


def guard_to_cube(
    guard: Guard, domains: dict[str, tuple[str, ...]]
) -> R.Cube:
    eq: dict[str, str] = {}
    ne: dict[str, set[str]] = {}
    for c in guard.clauses:
        if c.op == Op.EQ:
            eq[c.variable] = c.value
        else:
            ne.setdefault(c.variable, set()).add(c.value)
    return R.cube_from_clauses(eq, ne, domains)


# --- unknown_term (CHK-R3) ------------------------------------------------


@dataclass
class UnknownTermInfo:
    """Cards/effects with unknown terms, so semantic phases can exclude them.

    A card whose *guard* references an unknown variable/value has no
    well-defined region and is excluded from conflict / gap / dead-rule
    analysis. An *effect* on an unknown variable is dropped from the conflict
    write-set (its "value" has no domain, so write-write comparison is
    undefined) — this prevents one undeclared output variable from cascading
    into a swarm of false conflicts.
    """

    bad_guard_cards: set[str] = field(default_factory=set)  # "spec:card_id"
    bad_effect_vars: dict[str, set[str]] = field(default_factory=dict)


def check_unknown_terms(
    specs: list[Spec],
    domains: dict[str, tuple[str, ...]],
    entity_vars: dict[str, list[str]],
    result: CheckResult,
) -> UnknownTermInfo:
    info = UnknownTermInfo()

    def known_var(v: str) -> bool:
        return v in domains

    def known_val(var: str, val: str) -> bool:
        if val == UNCHANGED:
            return True
        return val in domains.get(var, ())

    def emit(spec, card, var, val, where) -> bool:
        """Emit an unknown_term finding if needed. Returns True if unknown."""
        if not known_var(var):
            result.findings.append(
                Finding(
                    kind="unknown_term",
                    severity=Severity.ERROR,
                    message=(
                        f"Unknown variable '{var}' in the {where} of "
                        f"{card.card_id} ({spec.name}); not in the merged "
                        f"vocabulary."
                    ),
                    location=card.location,
                )
            )
            return True
        if not known_val(var, val):
            result.findings.append(
                Finding(
                    kind="unknown_term",
                    severity=Severity.ERROR,
                    message=(
                        f"Unknown value '{val}' for variable '{var}' in the "
                        f"{where} of {card.card_id} ({spec.name}); not among "
                        f"[{', '.join(domains.get(var, ()))}]."
                    ),
                    location=card.location,
                )
            )
            return True
        return False

    for spec in specs:
        for card in spec.cards:
            key = f"{spec.name}:{card.card_id}"
            if card.kind == CardKind.REQUIREMENT:
                if card.guard:
                    for cl in card.guard.clauses:
                        if emit(spec, card, cl.variable, cl.value, "guard"):
                            info.bad_guard_cards.add(key)
                for e in card.effects:
                    if emit(spec, card, e.variable, e.value, "effect"):
                        info.bad_effect_vars.setdefault(key, set()).add(
                            e.variable
                        )
                if card.frame and card.frame not in entity_vars:
                    result.findings.append(
                        Finding(
                            kind="unknown_term",
                            severity=Severity.ERROR,
                            message=(
                                f"frame: {card.frame} in {card.card_id} names "
                                f"no known entity."
                            ),
                            location=card.location,
                        )
                    )
            elif card.kind in (CardKind.INVARIANT, CardKind.DONT_CARE):
                if card.invariant_guard:
                    for cl in card.invariant_guard.clauses:
                        if emit(spec, card, cl.variable, cl.value, "invariant"):
                            info.bad_guard_cards.add(key)
    return info


# --- duplicate_definition (CHK-R4) ----------------------------------------


def check_duplicate_definitions(specs: list[Spec], result: CheckResult) -> None:
    """A concept defined via `defines:` in two specs, neither importing it from
    a common interface."""
    # which specs define which concept
    concept_defs: dict[str, list[str]] = {}
    interface_specs = {s.name for s in specs if s.kind == "interface"}
    for spec in specs:
        concepts = spec.defines.get("concepts") if spec.defines else None
        if not concepts:
            continue
        for c in concepts:
            concept_defs.setdefault(c, []).append(spec.name)

    # imports: spec -> set of (from_spec, concept)
    def imports_from_interface(concept: str) -> bool:
        for spec in specs:
            for imp in spec.imports:
                frm = imp.get("from")
                use = imp.get("use") or []
                if frm in interface_specs and concept in use:
                    return True
        return False

    for concept, defining in concept_defs.items():
        if len(defining) > 1:
            if not imports_from_interface(concept):
                result.findings.append(
                    Finding(
                        kind="duplicate_definition",
                        severity=Severity.ERROR,
                        message=(
                            f"Concept '{concept}' is defined in multiple specs "
                            f"({', '.join(defining)}) without a shared "
                            f"interface import."
                        ),
                        location=", ".join(defining),
                    )
                )


# --- conflict (CHK-R1 / D9) -----------------------------------------------


@dataclass
class _Req:
    spec: str
    card: Card
    cube: R.Cube
    effects: tuple[Effect, ...]


def _render_situation(situation: dict[str, str]) -> str:
    parts = [f"{k} = {v}" for k, v in sorted(situation.items())]
    return ", ".join(parts)


def _witness_situation(
    cube: R.Cube, domains: dict[str, tuple[str, ...]]
) -> dict[str, str]:
    """Pick one concrete situation from a (non-empty) cube."""
    out: dict[str, str] = {}
    for var, vals in cube.as_dict().items():
        if vals:
            out[var] = sorted(vals)[0]
    return out


def check_conflicts(
    reqs: list[_Req],
    domains: dict[str, tuple[str, ...]],
    result: CheckResult,
) -> None:
    for i in range(len(reqs)):
        for j in range(i + 1, len(reqs)):
            a, b = reqs[i], reqs[j]
            if not R.overlaps(a.cube, b.cube, domains):
                continue
            # effects clash: same variable, different concrete value
            clash_var = _effects_clash(a.effects, b.effects)
            if clash_var is None:
                continue
            # override link in either direction?
            if (
                b.card.card_id in a.card.overrides
                or a.card.card_id in b.card.overrides
            ):
                continue
            overlap = R.intersect(a.cube, b.cube, domains)
            witness = _render_situation(_witness_situation(overlap, domains))
            va = _value_for(a.effects, clash_var)
            vb = _value_for(b.effects, clash_var)
            decisions = sorted(set(a.card.because) | set(b.card.because))
            dec = (
                f" (rationale: {', '.join(decisions)})" if decisions else ""
            )
            result.findings.append(
                Finding(
                    kind="conflict",
                    severity=Severity.ERROR,
                    message=(
                        f"{a.card.card_id} ({a.spec}) and {b.card.card_id} "
                        f"({b.spec}) have overlapping guards but assign "
                        f"'{clash_var}' differently ({a.card.card_id}: "
                        f"{clash_var} = {va}; {b.card.card_id}: {clash_var} = "
                        f"{vb}), with no overrides: link{dec}."
                    ),
                    witness=witness,
                )
            )


def _effects_clash(
    ea: tuple[Effect, ...], eb: tuple[Effect, ...]
) -> str | None:
    da = {e.variable: e.value for e in ea}
    db = {e.variable: e.value for e in eb}
    for var in da.keys() & db.keys():
        if da[var] != db[var]:
            # unchanged vs unchanged is compatible; unchanged vs concrete clashes
            return var
    return None


def _value_for(effects: tuple[Effect, ...], var: str) -> str:
    for e in effects:
        if e.variable == var:
            return e.value
    return "?"


# --- gap (CHK-R2 / D10) ---------------------------------------------------


def check_gaps(
    specs: list[Spec],
    reqs_by_spec: dict[str, list[_Req]],
    invariant_cubes: list[R.Cube],
    dontcare_cubes: list[R.Cube],
    criteria_cubes: list[tuple[Card, R.Cube]],
    domains: dict[str, tuple[str, ...]],
    result: CheckResult,
) -> None:
    """Gaps over the per-spec relevant projection (CHK-R2; bounded per build
    prompt to avoid the cross-spec product explosion — noted loudly)."""
    excluded = invariant_cubes + dontcare_cubes
    for spec in specs:
        reqs = reqs_by_spec.get(spec.name, [])
        if not reqs:
            continue
        # relevant projection: variables this spec's own requirement guards
        # constrain.
        proj_vars: list[str] = []
        for r in reqs:
            for cl in (r.card.guard.clauses if r.card.guard else []):
                if cl.variable not in proj_vars:
                    proj_vars.append(cl.variable)
        if not proj_vars:
            continue
        proj_vars.sort()
        covered = [r.cube for r in reqs]
        # restrict excluded/criteria cubes to this projection's variables
        uncovered = R.coverage_complement_cubes(
            proj_vars, covered, excluded, domains
        )
        result.projection_notes.append(
            f"- {spec.name}: projection over "
            f"[{', '.join(proj_vars)}] "
            f"({_proj_size(proj_vars, domains)} situations); "
            f"{len(reqs)} requirement guard(s)."
        )
        for cube in uncovered:
            if cube.is_empty():
                continue
            situation = _witness_situation(cube, domains)
            # criterion present? (CHK-R9)
            touching = [
                c.card_id
                for c, cc in criteria_cubes
                if R.overlaps(cube, cc, domains)
            ]
            q = _gap_question(cube, proj_vars, domains)
            extra = ""
            if touching:
                extra = (
                    f" (Judged attention exists here — criteria "
                    f"{', '.join(touching)} touch this region — but mechanical "
                    f"coverage does not.)"
                )
            result.findings.append(
                Finding(
                    kind="gap",
                    severity=Severity.WARNING,
                    message=q + extra,
                    witness=_render_situation(situation),
                )
            )


def _proj_size(proj_vars, domains) -> int:
    n = 1
    for v in proj_vars:
        n *= max(1, len(domains.get(v, ())))
    return n


def _gap_question(
    cube: R.Cube, proj_vars: list[str], domains: dict[str, tuple[str, ...]]
) -> str:
    """Phrase a cube as a designer question (D3), naming free variables."""
    d = cube.as_dict()
    fixed_parts = []
    free_parts = []
    for var in proj_vars:
        vals = d.get(var)
        full = set(domains.get(var, ()))
        if vals is None or set(vals) == full:
            free_parts.append(var)
        elif len(vals) == 1:
            fixed_parts.append(f"{var} = {next(iter(vals))}")
        else:
            fixed_parts.append(f"{var} ∈ {{{', '.join(sorted(vals))}}}")
    cond = " and ".join(fixed_parts) if fixed_parts else "(any situation)"
    free = ""
    if free_parts:
        free = f" (any {', '.join(free_parts)})"
    return f"What should happen when {cond}{free}?"


# --- dead_rule (CHK-R8) ---------------------------------------------------


def check_dead_rules(
    reqs: list[_Req],
    invariant_cubes: list[R.Cube],
    invariant_cards: list[Card],
    domains: dict[str, tuple[str, ...]],
    result: CheckResult,
) -> None:
    if not invariant_cubes:
        return
    for r in reqs:
        if R.cube_in_region(r.cube, invariant_cubes, domains):
            # find which invariants cover it
            covering = [
                ic.card_id
                for ic, cube in zip(invariant_cards, invariant_cubes)
                if R.overlaps(r.cube, cube, domains)
            ]
            result.findings.append(
                Finding(
                    kind="dead_rule",
                    severity=Severity.ERROR,
                    message=(
                        f"Requirement {r.card.card_id} ({r.spec}) can never "
                        f"fire: its guard region [{r.card.guard.render() if r.card.guard else ''}] "
                        f"lies entirely within the region excluded by invariant "
                        f"card(s) {', '.join(covering)}."
                    ),
                    location=r.card.location,
                )
            )


# --- stale_decision_ref (CHK-R5) ------------------------------------------


def check_stale_refs(specs: list[Spec], result: CheckResult) -> None:
    superseded_by: dict[str, list[str]] = {}
    for spec in specs:
        for card in spec.cards:
            if card.kind == CardKind.DECISION and card.superseded_by:
                superseded_by[card.card_id] = list(card.superseded_by)
    for spec in specs:
        for card in spec.cards:
            if card.kind == CardKind.REQUIREMENT and card.because:
                for dref in card.because:
                    if dref in superseded_by:
                        sup = ", ".join(superseded_by[dref])
                        result.findings.append(
                            Finding(
                                kind="stale_decision_ref",
                                severity=Severity.WARNING,
                                message=(
                                    f"{card.card_id} ({spec.name}) links "
                                    f"because: [[{dref}]], but {dref} is "
                                    f"superseded by {sup}. Re-point the "
                                    f"rationale at {sup}?"
                                ),
                                location=card.location,
                            )
                        )


# --- orphan_spec ----------------------------------------------------------


def check_orphans(specs: list[Spec], result: CheckResult) -> None:
    imported_by: dict[str, set[str]] = {s.name: set() for s in specs}
    imports_something: dict[str, bool] = {s.name: False for s in specs}
    for spec in specs:
        for imp in spec.imports:
            frm = imp.get("from")
            if frm:
                imports_something[spec.name] = True
                if frm in imported_by:
                    imported_by[frm].add(spec.name)
    for spec in specs:
        if not imports_something[spec.name] and not imported_by[spec.name]:
            result.findings.append(
                Finding(
                    kind="orphan_spec",
                    severity=Severity.WARNING,
                    message=(
                        f"Spec '{spec.name}' imports nothing and is imported by "
                        f"nothing; it is disconnected from the import diagram."
                    ),
                    location=spec.path,
                )
            )
