"""Region algebra over finite, enumerated vocabulary variables.

Situation space is a product of finite variable domains. A *cube* is an
axis-aligned region: for each variable it constrains, a set of allowed values
(a subset of that variable's domain). Variables a cube does not mention are
unconstrained (free over their whole domain).

A *region* is a union of cubes. We implement the operations the checker needs:

- ``Cube.satisfiable`` / overlap (do two cubes share a situation?),
- ``Cube.intersect``,
- containment of one cube/region inside a region (used for dead_rule and gap
  clustering),
- cube subtraction (one cube minus a region) by recursive splitting, which we
  use to enumerate and then *cluster* the uncovered part of situation space
  into maximal cubes (one designer question per cube — D3 / CHK-R2).

The whole module is domain-table driven: a ``Domains`` maps variable -> the
ordered tuple of its possible values. Cubes are normalised against it so that
"unconstrained" and "all values listed" are the same thing.
"""

from __future__ import annotations

from dataclasses import dataclass

Domains = dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class Cube:
    """An axis-aligned region: variable -> frozenset of allowed values.

    Empty mapping = the whole (sub)space. A variable mapped to the empty set
    makes the cube empty (unsatisfiable).
    """

    constraints: frozenset[tuple[str, frozenset[str]]]

    @staticmethod
    def make(mapping: dict[str, set[str] | frozenset[str]]) -> "Cube":
        return Cube(
            frozenset(
                (var, frozenset(vals)) for var, vals in mapping.items()
            )
        )

    @staticmethod
    def top() -> "Cube":
        """The unconstrained cube (whole space)."""
        return Cube(frozenset())

    def as_dict(self) -> dict[str, frozenset[str]]:
        return {var: vals for var, vals in self.constraints}

    def is_empty(self) -> bool:
        return any(len(vals) == 0 for _var, vals in self.constraints)

    def allowed(self, var: str, domain: Domains) -> frozenset[str]:
        d = self.as_dict()
        if var in d:
            return d[var]
        return frozenset(domain.get(var, ()))

    def variables(self) -> set[str]:
        return {var for var, _ in self.constraints}


def cube_from_clauses(
    eq: dict[str, str], ne: dict[str, set[str]], domains: Domains
) -> Cube:
    """Build a cube from equality / inequality literals over the domains.

    ``eq`` maps var -> required value; ``ne`` maps var -> set of forbidden
    values. A variable with both is intersected. Unknown values yield an empty
    constraint set (caller decides whether to treat that as unsat or as a
    separate unknown_term finding).
    """
    mapping: dict[str, set[str]] = {}
    vars_seen = set(eq) | set(ne)
    for var in vars_seen:
        dom = set(domains.get(var, ()))
        allowed = set(dom)
        if var in eq:
            allowed &= {eq[var]}
        if var in ne:
            allowed -= ne[var]
        mapping[var] = allowed
    return Cube.make(mapping)


def intersect(a: Cube, b: Cube, domains: Domains) -> Cube:
    """Intersection of two cubes over the shared domain."""
    da, db = a.as_dict(), b.as_dict()
    mapping: dict[str, set[str]] = {}
    for var in a.variables() | b.variables():
        va = set(da.get(var, domains.get(var, ())))
        vb = set(db.get(var, domains.get(var, ())))
        mapping[var] = va & vb
    return Cube.make(mapping)


def overlaps(a: Cube, b: Cube, domains: Domains) -> bool:
    """Do two cubes share at least one situation? (jointly satisfiable)."""
    return not intersect(a, b, domains).is_empty()


def cube_subset(a: Cube, b: Cube, domains: Domains) -> bool:
    """Is cube ``a`` entirely contained in cube ``b``?"""
    if a.is_empty():
        return True
    da, db = a.as_dict(), b.as_dict()
    for var in b.variables():
        bvals = db[var]
        avals = set(da.get(var, domains.get(var, ())))
        if not avals <= set(bvals):
            return False
    return True


def subtract(a: Cube, b: Cube, domains: Domains) -> list[Cube]:
    """``a`` minus ``b`` as a list of disjoint cubes.

    Standard orthogonal-range subtraction: for each variable that ``b``
    constrains, carve off the slice of ``a`` lying outside ``b``'s allowed set,
    then narrow ``a`` to ``b``'s set on that variable and continue.
    """
    if a.is_empty():
        return []
    inter = intersect(a, b, domains)
    if inter.is_empty():
        return [a] if not a.is_empty() else []

    result: list[Cube] = []
    da = a.as_dict()
    db = b.as_dict()
    current = dict(da)
    # Iterate in a deterministic (sorted) variable order: cube constraints are
    # frozensets, so dict order is hash-randomised across processes and would
    # make the gap clustering non-deterministic.
    for var in sorted(db):
        bvals = db[var]
        avals = set(current.get(var, domains.get(var, ())))
        outside = avals - set(bvals)
        if outside:
            piece = dict(current)
            piece[var] = outside
            piece_cube = Cube.make(piece)
            if not piece_cube.is_empty():
                result.append(_normalise(piece_cube, domains))
        # narrow to the intersection on this var for subsequent splits
        current[var] = avals & set(bvals)
        if not current[var]:
            break
    return result


def subtract_region(a: Cube, region: list[Cube], domains: Domains) -> list[Cube]:
    """``a`` minus a union of cubes."""
    pieces = [a] if not a.is_empty() else []
    for b in region:
        nxt: list[Cube] = []
        for p in pieces:
            nxt.extend(subtract(p, b, domains))
        pieces = nxt
        if not pieces:
            break
    return pieces


def cube_in_region(a: Cube, region: list[Cube], domains: Domains) -> bool:
    """Is cube ``a`` entirely covered by the union ``region``?"""
    leftover = subtract_region(a, region, domains)
    return all(c.is_empty() for c in leftover)


def _normalise(c: Cube, domains: Domains) -> Cube:
    """Drop constraints equal to the full domain (they are unconstrained)."""
    mapping: dict[str, set[str]] = {}
    for var, vals in c.as_dict().items():
        dom = set(domains.get(var, ()))
        if dom and set(vals) == dom:
            continue  # unconstrained — omit
        mapping[var] = set(vals)
    return Cube.make(mapping)


def enumerate_situations(
    variables: list[str], domains: Domains
) -> list[dict[str, str]]:
    """Full cross product of the given variables' domains. Use sparingly."""
    situations: list[dict[str, str]] = [{}]
    for var in variables:
        vals = domains.get(var, ())
        nxt: list[dict[str, str]] = []
        for s in situations:
            for v in vals:
                t = dict(s)
                t[var] = v
                nxt.append(t)
        situations = nxt
    return situations


def cube_contains_situation(
    cube: Cube, situation: dict[str, str], domains: Domains
) -> bool:
    d = cube.as_dict()
    for var, vals in d.items():
        if situation.get(var) not in vals:
            return False
    return True


def coverage_complement_cubes(
    variables: list[str],
    covered: list[Cube],
    excluded: list[Cube],
    domains: Domains,
) -> list[Cube]:
    """Maximal-ish cubes of the projection NOT covered and NOT excluded.

    We start from the full cube over ``variables`` and subtract the covered and
    excluded regions, yielding disjoint cubes. Each returned cube is one
    designer question (CHK-R2 / D3).
    """
    top = Cube.make({v: set(domains.get(v, ())) for v in variables})
    top = _normalise(top, domains)
    remaining = subtract_region(top, list(covered) + list(excluded), domains)
    return [_normalise(c, domains) for c in remaining if not c.is_empty()]
