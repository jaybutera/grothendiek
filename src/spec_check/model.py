"""Data model for the spec system.

Dataclasses for the parsed spec surface: Spec, Card (Requirement / Invariant /
Decision / DontCare / Criterion), Guard, Effect, plus Findings. The guard /
region algebra lives in ``region.py``; this module is pure data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# --- vocabulary -----------------------------------------------------------

#: Reserved value produced by frame desugaring. Clashes with any concrete
#: assignment to the same variable; compatible only with itself (D12).
UNCHANGED = "unchanged"


@dataclass(frozen=True)
class VocabEntry:
    """One ``variable: [values...]`` declaration, with provenance."""

    variable: str
    values: tuple[str, ...]
    spec: str
    entity: str  # derived from dotted prefix, or the variable name if bare


# --- guards and effects ---------------------------------------------------


class Op(Enum):
    EQ = "="
    NE = "!="


@dataclass(frozen=True)
class Clause:
    """A single guard literal: ``variable = value`` or ``variable != value``."""

    variable: str
    op: Op
    value: str

    def render(self) -> str:
        return f"{self.variable} {self.op.value} {self.value}"


@dataclass(frozen=True)
class Guard:
    """A conjunction of clauses — an axis-aligned region (a cube)."""

    clauses: tuple[Clause, ...]

    def render(self) -> str:
        if not self.clauses:
            return "(true)"
        return " and ".join(c.render() for c in self.clauses)


class EffectKind(Enum):
    TRANSITION = "->"  # state transition
    RESPONSE = "="  # response fact


@dataclass(frozen=True)
class Effect:
    variable: str
    kind: EffectKind
    value: str

    def render(self) -> str:
        return f"{self.variable} {self.kind.value} {self.value}"


# --- cards ----------------------------------------------------------------


class CardKind(Enum):
    REQUIREMENT = "requirement"
    INVARIANT = "invariant"
    DECISION = "decision"
    DONT_CARE = "dont_care"
    CRITERION = "criterion"


@dataclass
class Card:
    kind: CardKind
    card_id: str
    title: str
    spec: str
    line: int  # 1-based line of the heading, for locations

    # requirement fields
    guard: Guard | None = None
    effects: tuple[Effect, ...] = ()
    frame: str | None = None  # entity name
    overrides: tuple[str, ...] = ()  # card ids this card overrides
    because: tuple[str, ...] = ()  # decision ids referenced

    # invariant / dont-care
    invariant_guard: Guard | None = None

    # decision fields
    date: str | None = None
    supersedes: tuple[str, ...] = ()
    superseded_by: tuple[str, ...] = ()

    # parse diagnostics attached to this card (raw fragments that failed)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def location(self) -> str:
        return f"{self.spec} ({self.card_id})"


@dataclass
class Spec:
    name: str
    path: str
    kind: str | None  # e.g. "interface"
    imports: list[dict]  # raw {from, use|rename}
    vocabulary: dict[str, tuple[str, ...]]
    entities: dict[str, tuple[str, ...]]  # declared (currently none in repo)
    defines: dict[str, list[str]]  # concepts/relations/values
    cards: list[Card]
    raw_frontmatter: dict


# --- findings -------------------------------------------------------------


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Finding:
    kind: str  # conflict, gap, unknown_term, ...
    severity: Severity
    message: str
    # CHK-I1: every finding carries a pointer.
    witness: str | None = None  # English-rendered witness situation
    location: str | None = None  # file/card location

    @property
    def pointer_kind(self) -> str:
        if self.witness:
            return "witness"
        if self.location:
            return "location"
        return "none"

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "severity": self.severity.value,
            "message": self.message,
            "witness": self.witness,
            "location": self.location,
            "pointer": self.pointer_kind,
        }
