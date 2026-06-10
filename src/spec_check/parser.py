"""Parse spec markdown files into the model.

Frontmatter is plain YAML between ``---`` fences — we split it ourselves (no
frontmatter library) and hand the slice to PyYAML. Cards are ``##`` sections;
their kind is read from the heading shape.

Guard grammar (``when:``)::

    guard  := clause ( "and" clause )*
    clause := variable ("=" | "!=") value

Effects grammar (``then:``)::

    effects    := assignment ( "," assignment )* [ "—" annotation-prose ]
    assignment := variable "->" value | variable "=" value

Unparseable guards / effects do not raise — they attach a ``parse_errors``
fragment to the card so the checker can emit ``nonconforming_card``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import yaml

from .model import (  # noqa: E402

    Card,
    CardKind,
    Clause,
    Effect,
    EffectKind,
    Guard,
    Op,
    Spec,
)

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


class _SpecLoader(yaml.SafeLoader):
    """SafeLoader that keeps YAML 1.1 bool words (yes/no/on/off/true/false) as
    plain strings.

    Vocabulary value sets like ``[yes, no]`` are domain tokens, not booleans;
    PyYAML's default 1.1 resolver would coerce them to ``True``/``False`` and
    corrupt every domain. We strip the bool implicit resolver so those tokens
    survive as the strings the spec author wrote.
    """


# Remove the bool implicit resolver from our loader only.
for _ch in list("yYnNtTfFoO"):
    if _ch in _SpecLoader.yaml_implicit_resolvers:
        _SpecLoader.yaml_implicit_resolvers[_ch] = [
            (tag, regexp)
            for tag, regexp in _SpecLoader.yaml_implicit_resolvers[_ch]
            if tag != "tag:yaml.org,2002:bool"
        ]

# Heading shapes
_RE_REQUIREMENT = re.compile(r"^##\s+([A-Z][A-Za-z]*-R\d+)\s*:\s*(.*)$")
_RE_INVARIANT = re.compile(r"^##\s+(\S+)\s+\(invariant\)\s*:\s*(.*)$")
_RE_DONTCARE = re.compile(r"^##\s+(\S+)\s+\(dont[-_]care\)\s*:\s*(.*)$")
_RE_CRITERION = re.compile(r"^##\s+([A-Z][A-Za-z]*-C\d+)\s*:\s*(.*)$")
_RE_DECISION = re.compile(
    r"^##\s+(D\d+)\s+\(decision(?:,\s*([0-9-]+))?\)\s*:\s*(.*)$"
)
_RE_ANY_HEADING = re.compile(r"^##\s+(.*)$")

_RE_LINK = re.compile(r"\[\[(D\d+)\]\]")
_RE_SUPERSEDES = re.compile(r"supersedes:\s*(D\d+(?:\s*,\s*D\d+)*)")
_RE_SUPERSEDED_BY = re.compile(r"status:\s*superseded\s+by\s+(.*)")


@dataclass
class _RawCard:
    heading: str
    body_lines: list[str]
    line: int


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Empty dict if no frontmatter."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)
    data = yaml.load(fm_text, Loader=_SpecLoader) or {}
    if not isinstance(data, dict):
        data = {}
    return data, body


def _entity_of(variable: str) -> str:
    """Derive the entity from a dotted prefix; bare vars are their own entity."""
    return variable.split(".", 1)[0]


def _split_cards(body: str, fm_line_offset: int) -> list[_RawCard]:
    lines = body.split("\n")
    cards: list[_RawCard] = []
    current: _RawCard | None = None
    for i, line in enumerate(lines):
        if _RE_ANY_HEADING.match(line):
            if current is not None:
                cards.append(current)
            current = _RawCard(
                heading=line, body_lines=[], line=fm_line_offset + i + 1
            )
        elif current is not None:
            current.body_lines.append(line)
    if current is not None:
        cards.append(current)
    return cards


def _collect_field(body_lines: list[str], name: str) -> str | None:
    """Collect a ``name:`` field value, continuing across indented lines.

    A field ends at the next line that begins another known field at column 0,
    a blank line, or a heading. Continuation lines (indented or non-field) are
    folded in with single spaces.
    """
    field_re = re.compile(rf"^{re.escape(name)}:\s*(.*)$")
    other_field_re = re.compile(r"^[a-z][a-z_]*:\s")
    out: list[str] = []
    capturing = False
    for line in body_lines:
        if not capturing:
            m = field_re.match(line)
            if m:
                capturing = True
                if m.group(1).strip():
                    out.append(m.group(1).strip())
            continue
        # capturing
        if line.strip() == "":
            break
        if other_field_re.match(line) and not field_re.match(line):
            break
        out.append(line.strip())
    if not capturing:
        return None
    return " ".join(out).strip()


# --- guard / effect grammars ---------------------------------------------

_CLAUSE_RE = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*(!=|=)\s*(\S+)\s*$")


def parse_guard(text: str) -> tuple[Guard | None, list[str]]:
    """Parse a ``when:`` guard. Returns (guard, unparseable_fragments)."""
    text = text.strip()
    if not text:
        return None, ["<empty guard>"]
    parts = re.split(r"\band\b", text)
    clauses: list[Clause] = []
    errors: list[str] = []
    for part in parts:
        frag = part.strip()
        if not frag:
            continue
        m = _CLAUSE_RE.match(frag)
        if not m:
            errors.append(frag)
            continue
        var, op, val = m.group(1), m.group(2), m.group(3)
        clauses.append(
            Clause(var, Op.EQ if op == "=" else Op.NE, val.rstrip(","))
        )
    if not clauses:
        return None, errors or [text]
    return Guard(tuple(clauses)), errors


_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*(->|=)\s*(\S+)\s*$")


def parse_effects(text: str) -> tuple[tuple[Effect, ...], list[str]]:
    """Parse a ``then:`` effects clause.

    Per the v1 grammar (build prompt): parse the *leading* comma-separated
    assignments; an em-dash ends the formal part and the rest is annotation
    prose. We are lenient about trailing prose that is comma-separated rather
    than em-dash-separated (the spec's own hand-written cards do this, e.g.
    ``then: finding = conflict, naming both cards``): once a fragment fails to
    parse as an assignment, the remainder is treated as annotation prose and
    *not* flagged. A ``then:`` is nonconforming only when **no** leading
    assignment parses at all.
    """
    # Em-dash ends the formal part; the rest is annotation prose.
    formal = text.split("—", 1)[0].strip()
    if not formal:
        return (), ["<no leading assignment>"]
    effects: list[Effect] = []
    for part in formal.split(","):
        frag = part.strip()
        if not frag:
            continue
        m = _ASSIGN_RE.match(frag)
        if not m:
            # leading assignments end here; remainder is annotation prose
            break
        var, op, val = m.group(1), m.group(2), m.group(3)
        kind = EffectKind.TRANSITION if op == "->" else EffectKind.RESPONSE
        effects.append(Effect(var, kind, val))
    if not effects:
        return (), ["<no leading assignment>"]
    return tuple(effects), []


def _parse_links(text: str) -> tuple[str, ...]:
    return tuple(_RE_LINK.findall(text or ""))


def _parse_overrides(body_lines: list[str]) -> tuple[str, ...]:
    val = _collect_field(body_lines, "overrides")
    if not val:
        return ()
    return tuple(re.findall(r"[A-Z][A-Za-z]*-R\d+", val))


def _build_card(raw: _RawCard, spec_name: str) -> Card | None:
    heading = raw.heading
    body = raw.body_lines

    m = _RE_INVARIANT.match(heading)
    if m:
        card = Card(
            kind=CardKind.INVARIANT,
            card_id=m.group(1),
            title=m.group(2).strip(),
            spec=spec_name,
            line=raw.line,
        )
        inv = _collect_field(body, "invariant")
        if inv:
            guard, errs = parse_guard(_strip_invariant_prose(inv))
            card.invariant_guard = guard
            card.parse_errors.extend(errs)
        else:
            card.parse_errors.append("<missing invariant: field>")
        return card

    m = _RE_DONTCARE.match(heading)
    if m:
        card = Card(
            kind=CardKind.DONT_CARE,
            card_id=m.group(1),
            title=m.group(2).strip(),
            spec=spec_name,
            line=raw.line,
        )
        dc = _collect_field(body, "dont-care") or _collect_field(
            body, "dont_care"
        )
        if dc:
            guard, errs = parse_guard(_strip_invariant_prose(dc))
            card.invariant_guard = guard
            card.parse_errors.extend(errs)
        else:
            card.parse_errors.append("<missing dont-care: field>")
        return card

    m = _RE_DECISION.match(heading)
    if m:
        card = Card(
            kind=CardKind.DECISION,
            card_id=m.group(1),
            title=m.group(3).strip(),
            spec=spec_name,
            line=raw.line,
            date=m.group(2),
        )
        full = "\n".join([heading] + body)
        sm = _RE_SUPERSEDES.search(full)
        if sm:
            card.supersedes = tuple(
                re.findall(r"D\d+", sm.group(1))
            )
        sbm = _RE_SUPERSEDED_BY.search(full)
        if sbm:
            card.superseded_by = _parse_links(sbm.group(1)) or tuple(
                re.findall(r"D\d+", sbm.group(1))
            )
        return card

    m = _RE_CRITERION.match(heading)
    if m:
        card = Card(
            kind=CardKind.CRITERION,
            card_id=m.group(1),
            title=m.group(2).strip(),
            spec=spec_name,
            line=raw.line,
        )
        return card

    m = _RE_REQUIREMENT.match(heading)
    if m:
        card = Card(
            kind=CardKind.REQUIREMENT,
            card_id=m.group(1),
            title=m.group(2).strip(),
            spec=spec_name,
            line=raw.line,
        )
        when = _collect_field(body, "when")
        then = _collect_field(body, "then")
        frame = _collect_field(body, "frame")
        because = _collect_field(body, "because")
        if when is not None:
            guard, errs = parse_guard(when)
            card.guard = guard
            if errs:
                card.parse_errors.extend(
                    f"unparseable guard fragment: {e!r}" for e in errs
                )
        else:
            card.parse_errors.append("<missing when: field>")
        if then is not None:
            effects, errs = parse_effects(then)
            card.effects = effects
            if errs:
                card.parse_errors.extend(
                    f"unparseable effect fragment: {e!r}" for e in errs
                )
        else:
            card.parse_errors.append("<missing then: field>")
        if frame:
            card.frame = frame.strip()
        card.overrides = _parse_overrides(body)
        card.because = _parse_links(because or "")
        return card

    # Unknown heading shape: not a card we model (e.g. "## Resolved since...").
    return None


def _strip_invariant_prose(text: str) -> str:
    """Invariant lines mix a guard with an em-dash explanation. Keep the guard.

    E.g. ``finding.pointer != none — every emitted finding ...`` → the part
    before the em-dash.
    """
    return text.split("—", 1)[0].strip()


def parse_spec(path: str, text: str) -> Spec:
    fm, body = split_frontmatter(text)
    name = fm.get("spec") or path
    kind = fm.get("kind")
    imports = fm.get("imports") or []
    raw_vocab = fm.get("vocabulary") or {}
    vocabulary: dict[str, tuple[str, ...]] = {}
    for var, vals in raw_vocab.items():
        if isinstance(vals, list):
            vocabulary[var] = tuple(str(v) for v in vals)
        else:
            vocabulary[var] = (str(vals),)
    entities_raw = fm.get("entities") or {}
    entities: dict[str, tuple[str, ...]] = {
        e: tuple(vs) for e, vs in entities_raw.items()
    }
    defines = fm.get("defines") or {}

    # number of lines consumed by frontmatter, to offset card line numbers
    fm_lines = 0
    m = _FRONTMATTER_RE.match(text)
    if m:
        fm_lines = text[: m.start(2)].count("\n")

    raw_cards = _split_cards(body, fm_lines)
    cards: list[Card] = []
    for rc in raw_cards:
        c = _build_card(rc, name)
        if c is not None:
            cards.append(c)

    return Spec(
        name=name,
        path=path,
        kind=kind,
        imports=imports if isinstance(imports, list) else [],
        vocabulary=vocabulary,
        entities=entities,
        defines=defines if isinstance(defines, dict) else {},
        cards=cards,
        raw_frontmatter=fm,
    )
