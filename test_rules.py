import random

from analysis import analyze
from rules import INV_THRESHOLD, SMALL_N, recommend


def rec(values, **kw):
    return recommend(analyze(values), **kw)["algorithm"]


def test_sorted_goes_to_insertion():
    assert rec(list(range(10_000))) == "Insertion Sort"


def test_random_goes_to_quick():
    rng = random.Random(0)
    a = [rng.random() for _ in range(5_000)]
    assert rec(a) == "Quick Sort"


def test_small_n_goes_to_insertion():
    rng = random.Random(1)
    a = list(range(SMALL_N))
    rng.shuffle(a)
    assert rec(a) == "Insertion Sort"


def test_two_halves_not_insertion_despite_high_sortedness():
    n = 2_000
    a = list(range(n // 2 + 1, n + 1)) + list(range(1, n // 2 + 1))
    result = recommend(analyze(a))
    assert result["algorithm"] == "Quick Sort"
    assert any("wirken vorsortiert" in note for note in result["notes"])


def test_constraints():
    rng = random.Random(2)
    a = [rng.random() for _ in range(5_000)]
    assert rec(a, need_stable=True) == "Merge Sort"
    assert rec(a, low_memory=True) == "Heap Sort"
    result = recommend(analyze(a), need_stable=True, low_memory=True)
    assert result["algorithm"] == "Merge Sort"
    assert result["notes"]


def test_insertion_satisfies_constraints():
    # Insertion ist stabil und in-place, bleibt also trotz Vorgaben die Empfehlung
    assert rec(list(range(1_000)), need_stable=True, low_memory=True) == "Insertion Sort"


def test_mixed_types():
    assert rec([1, "a", 2]) is None


def test_threshold_boundary():
    assert 0 < INV_THRESHOLD < 1
