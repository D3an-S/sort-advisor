"""Regelwerk des Sort Advisors.

Eingabe sind die Merkmale aus analysis.analyze() und die Nutzervorgaben.
Ausgabe ist ein empfohlener Algorithmus mit Begründung.

Schwellen (gemessen mit benchmark_inv.py, Python 3.13, eigene Implementierungen
aus sorting.py, Testdaten: in Blöcken gemischte Listen, n = 500 bis 50.000):

    INV_THRESHOLD = 0.5
        Insertion Sort ist schneller als Merge, Quick und Heap, solange
        Inv / (n · log2 n) unter etwa 0,6 bis 0,8 liegt (Break-even je nach n).
        0,5 liegt bei allen gemessenen n darunter und ist damit eine
        konservative Wahl.
        Theorie dazu: Insertion braucht genau Inv Verschiebungen und höchstens
        Inv + n - 1 Vergleiche (Knuth, TAOCP Vol. 3, 5.2.1), die anderen
        Verfahren Θ(n log n).

    SMALL_N = 16
        Bei Zufallsdaten bis n ≈ 16 ist Insertion trotz vieler Inversionen
        schneller (gemessen: Laufzeitverhältnis 0,88 bei n = 16, 1,27 bei n = 32),
        weil die konstanten Faktoren der rekursiven Verfahren überwiegen.

Hinweis zum Speicher: Die Funktionen in sorting.py kopieren die Eingabe
jeweils in eine neue Liste. Die Aussagen zu "in-place" beziehen sich daher
auf den Algorithmus, nicht auf diese Python-Implementierung.
"""

INV_THRESHOLD = 0.5
SMALL_N = 16

# Eigenschaften der implementierten Algorithmen
PROPERTIES = {
    "Insertion Sort": {"stable": True,  "in_place": True},
    "Merge Sort":     {"stable": True,  "in_place": False},
    "Quick Sort":     {"stable": False, "in_place": True},
    "Heap Sort":      {"stable": False, "in_place": True},
}


def recommend(features, need_stable=False, low_memory=False):
    """Liefert {"algorithm": str | None, "reasons": [str], "notes": [str]}."""
    n = features["n"]
    reasons, notes = [], []

    if not features["is_comparable"]:
        return {
            "algorithm": None,
            "reasons": ["Die Spalte enthält gemischte Datentypen und lässt sich "
                        "nicht sinnvoll sortieren."],
            "notes": [],
        }

    if n < 2:
        return {
            "algorithm": "Insertion Sort",
            "reasons": ["Weniger als zwei Werte, es gibt nichts zu sortieren."],
            "notes": [],
        }

    c = features["inv_per_nlogn"]

    # Regel 1: Insertion bei kleinem n oder wenigen Inversionen.
    # Insertion ist stabil und in-place, erfüllt also beide Nutzervorgaben.
    if n <= SMALL_N:
        reasons.append(f"Sehr kleine Datenmenge (n = {n} ≤ {SMALL_N}). Hier ist "
                       f"Insertion Sort trotz O(n²) am schnellsten, weil der "
                       f"Verwaltungsaufwand der rekursiven Verfahren überwiegt.")
        algorithm = "Insertion Sort"
    elif c <= INV_THRESHOLD:
        reasons.append(f"Wenige Inversionen: Inv / (n · log₂ n) = {c:.2f} ≤ {INV_THRESHOLD}. "
                       f"Insertion Sort braucht genau so viele Verschiebungen, wie es "
                       f"Inversionen gibt, und ist damit schneller als die "
                       f"O(n log n)-Verfahren.")
        algorithm = "Insertion Sort"

    # Regel 2: Nutzervorgaben
    elif need_stable:
        algorithm = "Merge Sort"
        reasons.append("Stabilität ist gefordert. Merge Sort ist stabil und "
                       "garantiert O(n log n).")
        if low_memory:
            notes.append("Merge Sort braucht O(n) Zusatzspeicher. Ein Verfahren, das "
                         "stabil, in-place und O(n log n) zugleich ist, ist nicht "
                         "implementiert. Stabilität wurde vorgezogen, weil sie das "
                         "Ergebnis betrifft, der Speicher nur den Aufwand.")
    elif low_memory:
        algorithm = "Heap Sort"
        reasons.append("Speicher ist knapp. Heap Sort sortiert mit O(1) "
                       "Zusatzspeicher und garantiert O(n log n) auch im schlechtesten Fall.")
        notes.append("Quick Sort ist ebenfalls fast in-place (O(log n) Stack) und in "
                     "der Praxis meist schneller, hat aber einen O(n²)-Worst-Case.")

    # Regel 3: Standardfall
    else:
        algorithm = "Quick Sort"
        reasons.append(f"Viele Inversionen (Inv / (n · log₂ n) = {c:.2f} > {INV_THRESHOLD}) "
                       f"und keine besonderen Vorgaben. Quick Sort war in den Messungen "
                       f"bei solchen Daten am schnellsten.")

    # Erklärender Hinweis: wirkt vorsortiert, ist es für Insertion aber nicht
    if algorithm != "Insertion Sort" and n > SMALL_N and features["sortedness"] >= 0.9:
        notes.append(f"Die Daten wirken vorsortiert ({features['sortedness']:.0%} der "
                     f"Nachbarpaare stimmen, {features['runs']} Runs), enthalten aber "
                     f"viele Inversionen. Insertion Sort wäre hier trotzdem langsam.")

    return {"algorithm": algorithm, "reasons": reasons, "notes": notes}
