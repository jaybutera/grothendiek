"""Orchestrate a full check run over a directory of specs."""

from __future__ import annotations

import os
import re
import subprocess

from . import checker as C
from .model import Card, CardKind, Severity, Spec
from .parser import parse_spec


def discover_spec_files(root: str) -> list[str]:
    """Find spec markdown files: everything under specs/, plus system.md.

    We parse files that have YAML frontmatter declaring a `spec:` name.
    """
    paths: list[str] = []
    specs_dir = os.path.join(root, "specs")
    for dirpath, _dirs, files in os.walk(specs_dir):
        for f in sorted(files):
            if f.endswith(".md"):
                paths.append(os.path.join(dirpath, f))
    return sorted(paths)


def load_specs(root: str) -> list[Spec]:
    specs: list[Spec] = []
    for path in discover_spec_files(root):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        spec = parse_spec(os.path.relpath(path, root), text)
        # only keep files that actually declared a spec frontmatter
        if spec.raw_frontmatter.get("spec"):
            specs.append(spec)
    return specs


def _read_baseline_entities(root: str) -> dict[str, set[str]] | None:
    """Parse the machine-readable entity snapshot from git HEAD:REPORT.md.

    Returns None if no baseline (first tool run) or no snapshot block.
    """
    try:
        out = subprocess.run(
            ["git", "show", "HEAD:REPORT.md"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    m = re.search(
        r"<!--\s*spec-check:entities\s*(.*?)-->", out, re.DOTALL
    )
    if not m:
        return None
    snapshot: dict[str, set[str]] = {}
    for line in m.group(1).strip().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        ent, rest = line.split(":", 1)
        vars_ = {v.strip() for v in rest.split(",") if v.strip()}
        snapshot[ent.strip()] = vars_
    return snapshot


def check(root: str) -> C.CheckResult:
    result = C.CheckResult()
    specs = load_specs(root)
    result.specs = specs

    # 1. vocabulary merge
    domains = C.merge_vocabulary(specs, result)
    result.domains = domains

    # 2. nonconforming cards (exclude from semantics)
    excluded = C.check_nonconforming(specs, result)

    # 3. entities (derive + propose)
    C.build_entities(specs, domains, result)

    # 4. unknown_term (also tells us which cards/effects to exclude downstream)
    unknown = C.check_unknown_terms(specs, domains, result.entity_vars, result)

    # 5. duplicate_definition (concept-level via defines:)
    C.check_duplicate_definitions(specs, result)

    # 6. build desugared requirement set (skip excluded / nonconforming)
    reqs: list[C._Req] = []
    reqs_by_spec: dict[str, list[C._Req]] = {}
    invariant_cubes: list = []
    invariant_cards: list[Card] = []
    dontcare_cubes: list = []
    criteria_cubes: list[tuple[Card, object]] = []
    criteria: list[Card] = []

    for spec in specs:
        for card in spec.cards:
            key = f"{spec.name}:{card.card_id}"
            if card.kind == CardKind.REQUIREMENT:
                if key in excluded or card.guard is None or not card.effects:
                    continue
                # A guard with an unknown term has no well-defined region.
                if key in unknown.bad_guard_cards:
                    continue
                effects = C.desugar_frame(card, result.entity_vars, domains)
                # Drop effects on undeclared variables from semantic analysis
                # (their values have no domain, so write-write is undefined).
                bad_vars = unknown.bad_effect_vars.get(key, set())
                effects = tuple(e for e in effects if e.variable not in bad_vars)
                cube = C.guard_to_cube(card.guard, domains)
                req = C._Req(spec.name, card, cube, effects)
                reqs.append(req)
                reqs_by_spec.setdefault(spec.name, []).append(req)
            elif card.kind == CardKind.INVARIANT:
                if key in excluded or card.invariant_guard is None:
                    continue
                if key in unknown.bad_guard_cards:
                    continue
                invariant_cubes.append(
                    C.guard_to_cube(card.invariant_guard, domains)
                )
                invariant_cards.append(card)
            elif card.kind == CardKind.DONT_CARE:
                if key in excluded or card.invariant_guard is None:
                    continue
                dontcare_cubes.append(
                    C.guard_to_cube(card.invariant_guard, domains)
                )
            elif card.kind == CardKind.CRITERION:
                criteria.append(card)
    result.criteria = criteria

    # 7. conflict
    C.check_conflicts(reqs, domains, result)

    # 8. dead_rule
    C.check_dead_rules(reqs, invariant_cubes, invariant_cards, domains, result)

    # 9. gap (per-spec projection)
    C.check_gaps(
        specs,
        reqs_by_spec,
        invariant_cubes,
        dontcare_cubes,
        criteria_cubes,
        domains,
        result,
    )

    # 10. stale_decision_ref
    C.check_stale_refs(specs, result)

    # 11. orphan_spec
    C.check_orphans(specs, result)

    # 12. frame_strengthened (CHK-R11 / D15) — git baseline.
    # Per CHK-R11 the finding is about *framed* entities only: it names the
    # framed card. Entity growth with no frame over it strengthens nothing.
    framed: dict[str, list[str]] = {}
    for spec in specs:
        for card in spec.cards:
            if card.frame:
                framed.setdefault(card.frame, []).append(card.card_id)
    _check_frame_strengthened(root, result, framed)

    # 13. stratification lint (CHK-R13 / T9): a requirement guard may
    # never mention a finding variable — findings are write-only at their
    # own level. Invariant/dont-care cards are exempt (claims, not rules).
    finding_vars = set(result.entity_vars.get("finding", []))
    for spec in specs:
        for card in spec.cards:
            if card.kind is not CardKind.REQUIREMENT or card.guard is None:
                continue
            hit = [
                cl.variable
                for cl in card.guard.clauses
                if cl.variable in finding_vars
            ]
            if hit:
                result.findings.append(
                    C.Finding(
                        kind="unstratified_guard",
                        severity=Severity.ERROR,
                        message=(
                            f"Guard of {card.card_id} ({spec.name}) mentions "
                            f"finding variable(s) {', '.join(sorted(hit))} — "
                            f"findings are write-only at their own level "
                            f"(T9): a rule fired by reading the findings of "
                            f"its own run admits the liar."
                        ),
                        location=f"{spec.name} ({card.card_id})",
                    )
                )

    # 14. spec-as-config (CHK-R12 / D18): severities are read from the
    # spec corpus, not hardcoded. Well-founded: config is read before the
    # run's findings are classified; findings never feed back into config.
    _apply_spec_severities(specs, result)

    # sort findings: errors first, then by kind, for stable output
    order = {Severity.ERROR: 0, Severity.WARNING: 1}
    result.findings.sort(key=lambda f: (order[f.severity], f.kind, f.message))
    return result


def _apply_spec_severities(specs, result) -> None:
    sev_map: dict[str, Severity] = {}
    source = None
    for spec in specs:
        block = spec.raw_frontmatter.get("severities")
        if not isinstance(block, dict):
            continue
        source = spec.name
        for kind in block.get("error") or []:
            sev_map[str(kind)] = Severity.ERROR
        for kind in block.get("warning") or []:
            sev_map[str(kind)] = Severity.WARNING
    if not sev_map:
        result.notes.append(
            "severities: built-in defaults (no spec declares a "
            "`severities:` block)."
        )
        return
    result.notes.append(
        f"severities: read from spec '{source}' (CHK-R12 / D18) — the "
        f"checker is configured by the spec it checks."
    )
    unclassified: set[str] = set()
    for f in result.findings:
        if f.kind in sev_map:
            f.severity = sev_map[f.kind]
        else:
            unclassified.add(f.kind)
    for kind in sorted(unclassified):
        # Hardcoded ERROR by necessity: an unclassified kind cannot look up
        # its own severity — this is the one finding the config cannot govern.
        result.findings.append(
            C.Finding(
                kind="unclassified_finding_kind",
                severity=Severity.ERROR,
                message=(
                    f"The checker emitted finding kind '{kind}' but the "
                    f"spec's `severities:` block does not classify it — "
                    f"tool and spec have drifted. Add '{kind}' to the "
                    f"severities block in {source}."
                ),
                location=f"{source} (frontmatter severities:)",
            )
        )


def _check_frame_strengthened(
    root: str, result: C.CheckResult, framed: dict[str, list[str]]
) -> None:
    baseline = _read_baseline_entities(root)
    if baseline is None:
        result.baseline_note = (
            "baseline unavailable — first tool run (no machine-readable entity "
            "snapshot in HEAD:REPORT.md); frame_strengthened skipped."
        )
        return
    current = {
        ent: set(vs) for ent, vs in result.entity_vars.items()
    }
    grew = []
    for ent, card_ids in sorted(framed.items()):
        old = baseline.get(ent, set())
        new_attrs = current.get(ent, set()) - old
        if old and new_attrs:
            grew.append((ent, sorted(new_attrs), card_ids))
    if grew:
        for ent, attrs, card_ids in grew:
            cards = ", ".join(card_ids)
            result.findings.append(
                C.Finding(
                    kind="frame_strengthened",
                    severity=Severity.WARNING,
                    message=(
                        f"Entity '{ent}' gained attribute(s) "
                        f"{', '.join(attrs)} since the baseline REPORT — the "
                        f"frame on {cards} now also freezes them. Intended?"
                    ),
                    location=cards,
                )
            )
        result.baseline_note = "baseline: HEAD:REPORT.md entity snapshot."
    else:
        result.baseline_note = (
            "baseline: HEAD:REPORT.md entity snapshot — no frame growth "
            "on framed entities."
        )
