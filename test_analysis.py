import random
from itertools import combinations

import pytest

from analysis import (
    analyze, entropy_ratio, inversions, inversion_ratio, is_comparable,
    is_numeric, max_displacement, range_ratio, rem, runs, sortedness, value_range,
)


# --- naive Referenzimplementierungen zum Gegenprüfen -----------------------

def naive_inversions(a):
    return sum(1 for i, j in combinations(range(len(a)), 2) if a[i] > a[j])


def naive_rem(a):
    # längste nicht-fallende Teilfolge per O(n²)-DP
    if not a:
        return 0
    best = [1] * len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] <= a[i]:
                best[i] = max(best[i], best[j] + 1)
    return len(a) - max(best)


@pytest.mark.parametrize("seed", range(20))
def test_inversions_against_naive(seed):
    rng = random.Random(seed)
    a = [rng.randint(0, 10) for _ in range(rng.randint(0, 60))]
    assert inversions(a) == naive_inversions(a)


@pytest.mark.parametrize("seed", range(20))
def test_rem_against_naive(seed):
    rng = random.Random(seed)
    a = [rng.randint(0, 10) for _ in range(rng.randint(0, 60))]
    assert rem(a) == naive_rem(a)


# --- Randfälle -----------------------------------------------------------------

def test_sorted_list():
    a = list(range(100))
    assert runs(a) == 1
    assert sortedness(a) == 1.0
    assert inversion_ratio(a) == 0.0
    assert rem(a) == 0
    assert max_displacement(a) == 0


def test_reversed_list():
    a = list(range(100, 0, -1))
    assert runs(a) == 100
    assert sortedness(a) == 0.0
    assert inversion_ratio(a) == 1.0
    assert rem(a) == 99
    assert max_displacement(a) == 99


def test_one_large_element_in_front():
    # Nachbarpaar-Maß sagt fast sortiert, Inversionen und Verschiebung widersprechen
    n = 100
    a = [n] + list(range(1, n))
    assert sortedness(a) > 0.98
    assert inversions(a) == n - 1
    assert rem(a) == 1
    assert max_displacement(a) == n - 1


def test_duplicates_are_not_inversions():
    assert inversions([3, 3, 3, 3]) == 0
    assert max_displacement([3, 3, 3, 3]) == 0


def test_empty_and_single():
    for a in ([], [42]):
        f = analyze(a)
        assert f["n"] == len(a)
        assert f["inversion_ratio"] == 0.0
        assert f["rem_ratio"] == 0.0


def test_entropy():
    assert entropy_ratio([7] * 50) == 0.0
    assert entropy_ratio(list(range(64))) == pytest.approx(1.0)


def test_value_range():
    assert value_range([5, 1, 3]) == 5
    assert range_ratio([1, 2, 3, 4]) == 1.0
    assert value_range([1.5, 2.0]) is None
    assert value_range(["a", "b"]) is None


def test_types():
    assert not is_numeric([True, False])
    assert is_comparable(["b", "a"])
    assert not is_comparable([1, "a"])
    f = analyze([1, "a", 2])
    assert f["inversion_ratio"] is None
    assert f["duplicate_ratio"] == 0.0


def test_strings_work():
    f = analyze(["c", "a", "b"])
    assert f["inversion_ratio"] == pytest.approx(2 / 3)
