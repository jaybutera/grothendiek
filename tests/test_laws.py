"""The decidable theorems of specs/theory.md, as executable laws.

Every law is checked by brute force against point semantics over small
finite domains — in this setting the category theory is decidable, so the
theorems are tests. If a change to region.py or checker.py breaks the
subobject lattice (T3), the cover partition (T5), or the adjunctions
(T6/T7), this file goes red. That is the enforcement half of D19.
"""

from __future__ import annotations

import itertools

from spec_check import region as R
from spec_check.checker import _project_cube

DOMAINS = {"a": ("0", "1"), "b": ("x", "y", "z")}


def _points(domains):
    names = sorted(domains)
    for combo in itertools.product(*(domains[n] for n in names)):
        yield dict(zip(names, combo))


def _pts(cube: R.Cube, domains=DOMAINS) -> frozenset:
    cons = dict(cube.constraints)
    out = []
    for p in _points(domains):
        if all(p[v] in vals for v, vals in cons.items() if v in p):
            out.append(tuple(sorted(p.items())))
    return frozenset(out)


def _all_cubes(domains=DOMAINS):
    """Every axis-aligned cube over the domains (incl. unconstrained)."""
    per_var = []
    for v in sorted(domains):
        vals = domains[v]
        subsets = [None]  # unconstrained
        for r in range(1, len(vals) + 1):
            subsets.extend(frozenset(c) for c in itertools.combinations(vals, r))
        per_var.append([(v, s) for s in subsets])
    for combo in itertools.product(*per_var):
        yield R.Cube(frozenset((v, s) for v, s in combo if s is not None))


CUBES = list(_all_cubes())
TOP = frozenset(_pts(R.Cube(frozenset())))


# --- T3: the cube algebra is the subobject lattice ------------------------


def test_intersect_is_meet():
    for a, b in itertools.product(CUBES, CUBES):
        assert _pts(R.intersect(a, b, DOMAINS)) == _pts(a) & _pts(b)


def test_overlaps_iff_nonempty_meet():
    for a, b in itertools.product(CUBES, CUBES):
        assert R.overlaps(a, b, DOMAINS) == bool(_pts(a) & _pts(b))


def test_subset_is_order():
    for a, b in itertools.product(CUBES, CUBES):
        assert R.cube_subset(a, b, DOMAINS) == (_pts(a) <= _pts(b))


def test_subtract_is_relative_complement():
    for a, b in itertools.product(CUBES, CUBES):
        pieces = R.subtract(a, b, DOMAINS)
        pts = [_pts(p) for p in pieces]
        # disjoint pieces
        for i, j in itertools.combinations(range(len(pts)), 2):
            assert not (pts[i] & pts[j])
        # union is exactly A \ B
        union = frozenset().union(*pts) if pts else frozenset()
        assert union == _pts(a) - _pts(b)


def test_subtract_region_complement():
    import random

    rng = random.Random(7)
    for _ in range(200):
        a = rng.choice(CUBES)
        region = [rng.choice(CUBES) for _ in range(rng.randint(0, 4))]
        pieces = R.subtract_region(a, region, DOMAINS)
        union = frozenset().union(*(_pts(p) for p in pieces)) if pieces else frozenset()
        expect = _pts(a)
        for c in region:
            expect = expect - _pts(c)
        assert union == expect


# --- T5: coverage partitions the space -------------------------------------


def test_cover_partition():
    import random

    rng = random.Random(11)
    variables = sorted(DOMAINS)
    for _ in range(100):
        covered = [rng.choice(CUBES) for _ in range(rng.randint(0, 3))]
        excluded = [rng.choice(CUBES) for _ in range(rng.randint(0, 2))]
        uncovered = R.coverage_complement_cubes(
            variables, covered, excluded, DOMAINS
        )
        upts = (
            frozenset().union(*(_pts(c) for c in uncovered))
            if uncovered
            else frozenset()
        )
        cpts = (
            frozenset().union(*(_pts(c) for c in covered))
            if covered
            else frozenset()
        )
        epts = (
            frozenset().union(*(_pts(c) for c in excluded))
            if excluded
            else frozenset()
        )
        # gap = complement of the cover: partition of TOP (D10 / T5)
        assert upts == TOP - cpts - epts
        # returned cubes are pairwise disjoint witnesses
        pts = [_pts(c) for c in uncovered]
        for i, j in itertools.combinations(range(len(pts)), 2):
            assert not (pts[i] & pts[j])


# --- T6: the two query modes are the adjoint pair ---------------------------


def _touching(footprint, U):
    return R.overlaps(footprint, U, DOMAINS)


def _governing(footprint, U):
    return R.cube_subset(U, footprint, DOMAINS)


def test_governing_implies_touching_on_nonempty():
    for f, u in itertools.product(CUBES, CUBES):
        if _pts(u) and _governing(f, u):
            assert _touching(f, u)


def test_query_modes_monotone():
    # shrink the work region: governing grows, touching shrinks (T6).
    for f, u1, u2 in itertools.islice(
        itertools.product(CUBES, CUBES, CUBES), 0, None, 17
    ):
        if R.cube_subset(u1, u2, DOMAINS):
            if _governing(f, u2):
                assert _governing(f, u1) or not _pts(u1) or True
                # universal image: covering the bigger region covers the smaller
                assert _governing(f, u1)
            if _touching(f, u1):
                # existential image: touching the smaller touches the bigger
                assert _touching(f, u2)


# --- T7: existential projection is left adjoint to cylindrification --------


def test_projection_adjunction():
    proj_vars = {"a"}
    proj_domains = {"a": DOMAINS["a"]}
    for a_cube, b_cube in itertools.product(CUBES, CUBES):
        # B must be a cube of the projected space (constraints only on 'a')
        if {v for v, _ in b_cube.constraints} - proj_vars:
            continue
        lhs = R.cube_subset(
            _project_cube(a_cube, proj_vars), b_cube, proj_domains
        )
        # cylinder of B = same constraints read in the full space
        rhs = R.cube_subset(a_cube, b_cube, DOMAINS)
        assert lhs == rhs, (a_cube, b_cube)
