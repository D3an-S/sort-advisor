"""Messung der Inv-Schwelle für die Insertion-Sort-Regel.

Theorie: Insertion Sort braucht genau Inv Verschiebungen und höchstens
Inv + n - 1 Vergleiche (Knuth, TAOCP Vol. 3, 5.2.1). Merge, Quick und
Heap brauchen Θ(n log n). Insertion lohnt sich also, solange

    a · (n + Inv)  <  b · n · log2(n)

gilt. Die Konstanten a und b hängen von der Implementierung ab,
deshalb wird die Schwelle hier gemessen und als

    c = Inv / (n · log2 n)

am Break-even-Punkt angegeben.

Testdaten: sortierte Liste, die in Blöcken der Breite w gemischt wird.
Erwartete Inversionen ≈ n · (w - 1) / 4, also über w gut steuerbar.

Aufruf:  python benchmark_inv.py            (dauert ca. 1-2 Minuten)
Ausgabe: Tabelle auf der Konsole und benchmark_inv.csv
"""

import csv
import random
import time
from math import log2

from analysis import inversions
from sorting import ALGORITHMS

SIZES = [500, 1000, 2000, 5000]
WIDTHS = [2, 4, 8, 16, 32, 64, 128, 256, 512]
REPEATS = 5
SEED = 42


def block_shuffled(n, w, rng):
    a = list(range(n))
    for lo in range(0, n, w):
        block = a[lo:lo + w]
        rng.shuffle(block)
        a[lo:lo + w] = block
    return a


def best_time(fn, data, repeats):
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn(data)
        best = min(best, time.perf_counter() - start)
    return best


def main():
    rng = random.Random(SEED)
    rows = []
    others = {k: v for k, v in ALGORITHMS.items() if k != "Insertion Sort"}

    print(f"{'n':>6} {'w':>5} {'c=Inv/(n log n)':>16} {'Insertion':>10} {'bester Rest':>12}  schneller")
    for n in SIZES:
        for w in WIDTHS:
            if w > n:
                continue
            data = block_shuffled(n, w, rng)
            inv = inversions(data)
            c = inv / (n * log2(n))
            t_ins = best_time(ALGORITHMS["Insertion Sort"], data, REPEATS)
            t_rest = {name: best_time(fn, data, REPEATS) for name, fn in others.items()}
            best_name = min(t_rest, key=t_rest.get)
            winner = "Insertion" if t_ins < t_rest[best_name] else best_name
            rows.append({
                "n": n, "w": w, "inversions": inv, "c": round(c, 4),
                "insertion_ms": round(t_ins * 1000, 3),
                "best_other": best_name, "best_other_ms": round(t_rest[best_name] * 1000, 3),
                **{f"{k}_ms": round(v * 1000, 3) for k, v in t_rest.items()},
                "winner": winner,
            })
            print(f"{n:>6} {w:>5} {c:>16.3f} {t_ins*1000:>9.2f}ms {t_rest[best_name]*1000:>10.2f}ms  {winner}")

    with open("benchmark_inv.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Break-even je n: lineare Interpolation in log(c) zwischen letztem Sieg und erster Niederlage
    print("\nBreak-even je n:")
    for n in SIZES:
        r = [x for x in rows if x["n"] == n]
        for prev, nxt in zip(r, r[1:]):
            if prev["winner"] == "Insertion" and nxt["winner"] != "Insertion":
                # Verhältnis Insertion/Rest um 1 interpolieren
                q1 = prev["insertion_ms"] / prev["best_other_ms"]
                q2 = nxt["insertion_ms"] / nxt["best_other_ms"]
                t = (1 - q1) / (q2 - q1)
                c_star = prev["c"] * (nxt["c"] / prev["c"]) ** t
                print(f"  n = {n:>5}:  c* ≈ {c_star:.2f}")
                break


if __name__ == "__main__":
    main()
