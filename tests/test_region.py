"""Unit tests for the cube / region algebra — the mathematical core."""

from __future__ import annotations

from spec_check import region as R

DOMAINS = {
    "user.state": ("active", "suspended", "closed"),
    "sub.state": ("active", "paused", "cancelled"),
    "event": ("renewal_due", "payment_retry"),
}


def cube(**kw):
    return R.Cube.make({k: ({v} if isinstance(v, str) else set(v)) for k, v in kw.items()})


def test_top_overlaps_everything():
    c = cube(**{"user.state": "active"})
    assert R.overlaps(R.Cube.top(), c, DOMAINS)


def test_disjoint_on_one_var_no_overlap():
    a = cube(**{"user.state": "active"})
    b = cube(**{"user.state": "suspended"})
    assert not R.overlaps(a, b, DOMAINS)


def test_overlap_on_free_variable():
    # a constrains user.state only; b constrains sub.state only -> overlap
    a = cube(**{"user.state": "suspended"})
    b = cube(**{"sub.state": "paused"})
    assert R.overlaps(a, b, DOMAINS)
    inter = R.intersect(a, b, DOMAINS)
    d = inter.as_dict()
    assert d["user.state"] == frozenset({"suspended"})
    assert d["sub.state"] == frozenset({"paused"})


def test_intersect_empty():
    a = cube(**{"user.state": "active"})
    b = cube(**{"user.state": "closed"})
    assert R.intersect(a, b, DOMAINS).is_empty()


def test_cube_subset():
    whole = R.Cube.top()
    part = cube(**{"user.state": "active"})
    assert R.cube_subset(part, whole, DOMAINS)
    assert not R.cube_subset(whole, part, DOMAINS)


def test_cube_subset_multi_value():
    a = cube(**{"user.state": "active"})
    b = cube(**{"user.state": {"active", "suspended"}})
    assert R.cube_subset(a, b, DOMAINS)
    assert not R.cube_subset(b, a, DOMAINS)


def test_subtract_partitions():
    whole = R.Cube.make({"user.state": set(DOMAINS["user.state"])})
    minus = cube(**{"user.state": "active"})
    pieces = R.subtract(whole, minus, DOMAINS)
    # remaining = suspended + closed, as a single cube
    assert len(pieces) == 1
    vals = pieces[0].as_dict()["user.state"]
    assert vals == frozenset({"suspended", "closed"})


def test_subtract_two_dimensions():
    # full 2D space minus one corner -> should remain covered by complement
    variables = ["user.state", "sub.state"]
    top = R.Cube.make({v: set(DOMAINS[v]) for v in variables})
    corner = cube(**{"user.state": "active", "sub.state": "active"})
    pieces = R.subtract(top, corner, DOMAINS)
    # every situation except the corner must be in some piece
    total = 0
    for s in R.enumerate_situations(variables, DOMAINS):
        in_piece = any(
            R.cube_contains_situation(p, s, DOMAINS) for p in pieces
        )
        is_corner = s["user.state"] == "active" and s["sub.state"] == "active"
        assert in_piece == (not is_corner), s
        total += 1
    assert total == 9


def test_cube_in_region():
    variables = ["user.state"]
    region = [
        cube(**{"user.state": "active"}),
        cube(**{"user.state": {"suspended", "closed"}}),
    ]
    whole = cube(**{"user.state": {"active", "suspended", "closed"}})
    assert R.cube_in_region(whole, region, DOMAINS)


def test_coverage_complement():
    variables = ["user.state", "sub.state"]
    covered = [cube(**{"user.state": "active"})]
    excluded = [cube(**{"user.state": "closed"})]
    comp = R.coverage_complement_cubes(variables, covered, excluded, DOMAINS)
    # remaining = user.state == suspended (any sub.state)
    sits = []
    for s in R.enumerate_situations(variables, DOMAINS):
        if any(R.cube_contains_situation(c, s, DOMAINS) for c in comp):
            sits.append(s)
    assert all(s["user.state"] == "suspended" for s in sits)
    assert len(sits) == 3  # 3 sub.states


def test_cube_from_clauses_ne():
    c = R.cube_from_clauses({}, {"user.state": {"closed"}}, DOMAINS)
    d = c.as_dict()
    assert d["user.state"] == frozenset({"active", "suspended"})


def test_disjoint_subtract_returns_self():
    a = cube(**{"user.state": "active"})
    b = cube(**{"user.state": "closed"})
    pieces = R.subtract(a, b, DOMAINS)
    assert len(pieces) == 1
    assert pieces[0].as_dict()["user.state"] == frozenset({"active"})
