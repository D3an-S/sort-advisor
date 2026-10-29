"""Merkmalsanalyse einer Werteliste für den Sort Advisor.

Berechnet werden nur Merkmale, die bei den implementierten Algorithmen
(Insertion, Merge, Quick, Heap) eine Empfehlung ändern oder sie erklären:

    n               Anzahl Werte
    sortedness      Anteil Nachbarpaare in richtiger Reihenfolge.
                    Lässt sich in das Maß Runs (Mannila 1985) umrechnen:
                    Runs = (n - 1) · (1 - sortedness) + 1
    inversions      Anzahl Paare (i, j) mit i < j und a[i] > a[j]
                    (Knuth, TAOCP Vol. 3, 5.1.1; Maß Inv bei Mannila 1985).
                    Insertion Sort braucht genau Inv Verschiebungen (TAOCP 5.2.1).
    inv_per_nlogn   Inv / (n · log2 n), Grundlage der Insertion-Regel in rules.py
    duplicate_ratio Anteil doppelter Werte

Alle Funktionen laufen in O(n) oder O(n log n).
"""

from math import log2


# ---------------------------------------------------------------------------
# Datentyp
# ---------------------------------------------------------------------------

def _is_number(v):
    # bool ist in Python eine Unterklasse von int, soll aber nicht als Zahl zählen
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_numeric(values):
    return len(values) > 0 and all(_is_number(v) for v in values)


def is_comparable(values):
    """True, wenn sich alle Werte untereinander vergleichen lassen
    (nur Zahlen oder nur Texte). Bei gemischten Spalten würde
    Python beim Vergleich einen TypeError werfen."""
    return is_numeric(values) or all(isinstance(v, str) for v in values)


def length(values):
    return len(values)


# ---------------------------------------------------------------------------
# Vorsortiertheit
# ---------------------------------------------------------------------------

def runs(values):
    """Anzahl maximal aufsteigender Runs (Mannila 1985).
    Eine sortierte Liste hat 1 Run, eine streng absteigende n Runs."""
    if not values:
        return 0
    return 1 + sum(1 for i in range(len(values) - 1) if values[i] > values[i + 1])


def sortedness(values):
    """Anteil der Nachbarpaare mit a[i] <= a[i+1]."""
    n = len(values)
    if n < 2:
        return 1.0
    counter = sum(1 for i in range(n - 1) if values[i] <= values[i + 1])
    return counter / (n - 1)


def inversions(values):
    """Anzahl Inversionen, gezählt beim Zusammenführen in einem iterativen
    Merge Sort, O(n log n). Wird ein Element aus der rechten Hälfte
    übernommen, ist es kleiner als alle noch übrigen links, also kommen
    (mid - i) Inversionen hinzu. Gleiche Werte zählen nicht als Inversion."""
    a = list(values)
    n = len(a)
    buf = [None] * n
    count = 0
    width = 1
    while width < n:
        for lo in range(0, n, 2 * width):
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            i, j, k = lo, mid, lo
            while i < mid and j < hi:
                if a[i] <= a[j]:
                    buf[k] = a[i]; i += 1
                else:
                    buf[k] = a[j]; j += 1
                    count += mid - i
                k += 1
            while i < mid:
                buf[k] = a[i]; i += 1; k += 1
            while j < hi:
                buf[k] = a[j]; j += 1; k += 1
        a, buf = buf, a
        width *= 2
    return count


def inversion_ratio(values, inv=None):
    """Inversionen normiert auf das Maximum n(n-1)/2.
    0 = sortiert, 1 = streng absteigend. Nur zur Anzeige."""
    n = len(values)
    if n < 2:
        return 0.0
    if inv is None:
        inv = inversions(values)
    return inv / (n * (n - 1) / 2)


def inv_per_nlogn(values, inv=None):
    """Inv / (n · log2 n). Vergleicht den Aufwand von Insertion Sort
    (≈ n + Inv) mit dem der O(n log n)-Verfahren."""
    n = len(values)
    if n < 2:
        return 0.0
    if inv is None:
        inv = inversions(values)
    return inv / (n * log2(n))


# ---------------------------------------------------------------------------
# Duplikate
# ---------------------------------------------------------------------------

def duplicates(values):
    if not values:
        return 0.0
    return 1 - len(set(values)) / len(values)


# ---------------------------------------------------------------------------
# Gesamtanalyse
# ---------------------------------------------------------------------------

def analyze(values):
    comparable = is_comparable(values)
    features = {
        "n": len(values),
        "is_numeric": is_numeric(values),
        "is_comparable": comparable,
        "duplicate_ratio": duplicates(values),
        "sortedness": None,
        "runs": None,
        "inversions": None,
        "inversion_ratio": None,
        "inv_per_nlogn": None,
    }
    if comparable:
        inv = inversions(values)
        features.update({
            "sortedness": sortedness(values),
            "runs": runs(values),
            "inversions": inv,
            "inversion_ratio": inversion_ratio(values, inv),
            "inv_per_nlogn": inv_per_nlogn(values, inv),
        })
    return features
