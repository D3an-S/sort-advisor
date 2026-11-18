"""Benchmark für Kapitel 6 des Projektberichts (Sort Advisor).

Drei Experimente, alle mit den unveränderten Implementierungen aus sorting.py:

    A  Skalierung      Zufallsdaten, n = 1.000 bis 100.000
    B  Vorsortiertheit Laufzeit über c = Inv / (n · log2 n), zwei Arten von
                       Unordnung, die NICHT zur Kalibrierung der Schwelle
                       dienten (dort: blockweise gemischte Folgen)
    C  Trefferquote    Raster aus Größe × Datenart × Anforderungen:
                       Ist das empfohlene Verfahren das schnellste zulässige?

Aufruf (aus dem Repository-Wurzelverzeichnis):

    python benchmarks/benchmark.py            # vollständige Messung
    python benchmarks/benchmark.py --quick    # Schnelltest, nicht für den Bericht

Ausgabe in benchmarks/results/: je Experiment eine CSV-Datei, meta.json mit
Hardware und Python-Version, summary.txt und (falls matplotlib installiert ist)
die Diagramme als PDF und PNG.
"""

import argparse
import csv
import gc
import json
import platform
import random
import statistics
import sys
import time
from math import log2
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis import analyze, inversions  # noqa: E402
from rules import INV_THRESHOLD, PROPERTIES, SMALL_N, recommend  # noqa: E402
from sorting import ALGORITHMS  # noqa: E402

SEED = 42
ALGOS = list(ALGORITHMS)
BUILTIN = "sorted() (Timsort, C)"  # nur als Bezugsgröße in Experiment A

# Insertion Sort wird nicht gemessen, wenn die Eingabe mehr Inversionen enthält.
# 2 · 10^7 Verschiebungen dauern in reinem Python bereits mehrere Sekunden und
# liegen bei jedem gemessenen n weit über dem Gleichstand mit den übrigen
# Verfahren. Die Auslassung wird in den CSV-Dateien als leeres Feld vermerkt.
INSERTION_INV_LIMIT = 20_000_000

# Zwei Laufzeiten gelten als Gleichstand, wenn sie höchstens 5 % auseinander
# liegen (Messrauschen). Die strenge Trefferquote wird zusätzlich ausgewiesen.
TIE_TOLERANCE = 1.05


# ---------------------------------------------------------------------------
# Zeitmessung
# ---------------------------------------------------------------------------

def _batch(sort_fn, data, number):
    start = time.perf_counter()
    for _ in range(number):
        sort_fn(data)
    return time.perf_counter() - start


def _calibrate(sort_fn, data, min_batch):
    """Anzahl Aufrufe je Paket, sodass ein Paket mindestens min_batch dauert."""
    number = 1
    while True:
        elapsed = _batch(sort_fn, data, number)
        if elapsed >= min_batch or number >= 1_000_000:
            return number
        number = max(number * 2, int(number * min_batch / max(elapsed, 1e-9)) + 1)


def measure_functions(functions, data, runs, min_batch=0.02):
    """Median der Laufzeit eines Aufrufs in Sekunden, je Funktion.

    Kurze Aufrufe werden zu Paketen gebündelt. Die Läufe sind verschränkt:
    Jede Runde misst alle Funktionen einmal nacheinander. Eine kurzzeitige
    Störung des Rechners trifft so höchstens einzelne Runden aller Verfahren
    und fällt im Median heraus, statt ein einzelnes Verfahren zu verfälschen.
    Die Garbage Collection ist während der Messung aus.
    """
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        number = {name: _calibrate(fn, data, min_batch) for name, fn in functions.items()}
        samples = {name: [] for name in functions}
        for _ in range(runs):
            for name, fn in functions.items():
                samples[name].append(_batch(fn, data, number[name]) / number[name])
    finally:
        if gc_was_enabled:
            gc.enable()
    return {name: statistics.median(v) for name, v in samples.items()}


def measure_all(data, runs, inv=None, extra=None):
    """Laufzeit aller vier Verfahren, None für übersprungenes Insertion Sort.
    extra: weitere Funktionen, die unter denselben Bedingungen mitlaufen."""
    if inv is None:
        inv = inversions(data)
    expected = sorted(data)
    functions = {}
    for name, fn in ALGORITHMS.items():
        if name == "Insertion Sort" and inv > INSERTION_INV_LIMIT:
            continue
        assert fn(data) == expected, f"{name} sortiert falsch"
        functions[name] = fn
    functions.update(extra or {})
    measured = measure_functions(functions, data, runs)
    return {name: measured.get(name) for name in list(ALGORITHMS) + list(extra or {})}


# ---------------------------------------------------------------------------
# Testdaten
# ---------------------------------------------------------------------------

def random_data(n, rng):
    return [rng.random() for _ in range(n)]


def adjacent_swaps(n, target_inv, rng):
    """Sortierte Folge, durch zufällige Nachbarvertauschungen gestört, bis sie
    genau target_inv Inversionen enthält (lokale Unordnung)."""
    a = list(range(n))
    inv = 0
    while inv < target_inv:
        i = rng.randrange(n - 1)
        if a[i] < a[i + 1]:
            inv += 1
        else:
            inv -= 1
        a[i], a[i + 1] = a[i + 1], a[i]
    return a


def displaced_elements(n, target_inv, rng):
    """Sortierte Folge, aus der einzelne Elemente an zufällige Positionen
    versetzt werden, bis mindestens target_inv Inversionen erreicht sind
    (wenige Ausreißer, weite Wege). Ein Versetzen um d Stellen erzeugt in
    einer sortierten Folge d Inversionen; da sich Versetzungen überlagern,
    wird nachgezählt und bei Bedarf weiter versetzt."""
    a = list(range(n))
    inv = 0
    while inv < target_inv:
        budget = target_inv - inv
        while budget > 0:
            i = rng.randrange(n)
            j = rng.randrange(n)
            if i == j:
                continue
            a.insert(j, a.pop(i))
            budget -= abs(i - j)
        inv = inversions(a)
    return a


def two_halves(n):
    """⟨n/2+1, …, n, 1, …, n/2⟩: zwei Runs, aber n²/4 Inversionen (Kap. 3)."""
    return list(range(n // 2 + 1, n + 1)) + list(range(1, n // 2 + 1))


def target_inversions(n, c):
    """Inversionen für das gewünschte c, begrenzt auf 80 % des Maximums
    n(n-1)/2, damit kleine n erreichbar bleiben. Der tatsächlich erreichte
    Wert von c steht in den CSV-Dateien."""
    return min(int(c * n * log2(n)), int(0.8 * n * (n - 1) / 2))


# ---------------------------------------------------------------------------
# Experiment A: Skalierung
# ---------------------------------------------------------------------------

def experiment_scaling(sizes, runs):
    rows = []
    for n in sizes:
        data = random_data(n, random.Random(SEED))
        times = measure_all(data, runs, extra={BUILTIN: sorted})
        rows.append({"n": n, **{k: _ms(v) for k, v in times.items()}})
        print(f"  A  n = {n:>7}: " + _fmt_times(times))
    return rows


# ---------------------------------------------------------------------------
# Experiment B: Vorsortiertheit
# ---------------------------------------------------------------------------

DISORDER = {
    "Nachbarvertauschungen": adjacent_swaps,
    "Versetzte Elemente": displaced_elements,
}


def experiment_presorted(sizes, c_values, runs):
    rows = []
    for kind, make in DISORDER.items():
        for n in sizes:
            for c_target in c_values:
                data = make(n, target_inversions(n, c_target), random.Random(SEED))
                inv = inversions(data)
                c = inv / (n * log2(n))
                times = measure_all(data, runs, inv)
                rows.append({"disorder": kind, "n": n, "c_target": c_target,
                             "c": round(c, 4), "inversions": inv,
                             **{k: _ms(v) for k, v in times.items()}})
                print(f"  B  {kind:<22} n = {n:>6} c = {c:5.2f}: " + _fmt_times(times))
    return rows


def break_even(rows, kind, n):
    """Kleinstes c, ab dem Insertion Sort nicht mehr das schnellste Verfahren
    ist, linear zwischen den beiden benachbarten Messpunkten interpoliert."""
    pts = sorted((r for r in rows if r["disorder"] == kind and r["n"] == n),
                 key=lambda r: r["c"])
    prev = None
    for r in pts:
        ins = r["Insertion Sort"]
        if ins is None:
            break
        best_other = min(r[a] for a in ALGOS if a != "Insertion Sort")
        diff = ins - best_other
        if diff > 0:
            if prev is None:
                return r["c"]
            c0, d0 = prev
            return c0 + (r["c"] - c0) * (-d0) / (diff - d0)
        prev = (r["c"], diff)
    return None


# ---------------------------------------------------------------------------
# Experiment C: Trefferquote
# ---------------------------------------------------------------------------

REQUIREMENTS = [
    ("keine", False, False),
    ("stabil", True, False),
    ("Speicher knapp", False, True),
    ("stabil + Speicher knapp", True, True),
]


def admissible(need_stable, low_memory):
    """Zulässige Verfahren nach Kap. 3: stabil, falls gefordert, und O(1)
    Zusatzspeicher, falls der Speicher knapp ist. Quick Sort benötigt
    O(log n) und ist bei knappem Speicher daher nicht zulässig."""
    o1_memory = {"Insertion Sort", "Heap Sort"}
    return [a for a in ALGOS
            if (not need_stable or PROPERTIES[a]["stable"])
            and (not low_memory or a in o1_memory)]


def hitrate_cases(sizes):
    def strings(n, rng):
        return ["".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=8)) for _ in range(n)]

    kinds = {
        "zufällig": lambda n, rng: random_data(n, rng),
        "sortiert": lambda n, rng: list(range(n)),
        "absteigend": lambda n, rng: list(range(n, 0, -1)),
        "lokal gestört (c ≈ 0,25)": lambda n, rng: adjacent_swaps(n, target_inversions(n, 0.25), rng),
        "Ausreißer (c ≈ 0,4)": lambda n, rng: displaced_elements(n, target_inversions(n, 0.4), rng),
        "lokal gestört (c ≈ 1)": lambda n, rng: adjacent_swaps(n, target_inversions(n, 1.0), rng),
        "Ausreißer (c ≈ 2)": lambda n, rng: displaced_elements(n, target_inversions(n, 2.0), rng),
        "zwei Hälften": lambda n, rng: two_halves(n),
        "wenige verschiedene Werte": lambda n, rng: [rng.randrange(10) for _ in range(n)],
        "alle gleich": lambda n, rng: [7] * n,
        "Texte, zufällig": strings,
    }
    for n in sizes:
        for kind, make in kinds.items():
            yield n, kind, make(n, random.Random(SEED))


def experiment_hitrate(sizes, runs):
    rows = []
    for n, kind, data in hitrate_cases(sizes):
        features = analyze(data)
        times = measure_all(data, runs, features["inversions"])
        print(f"  C  n = {n:>6} {kind:<28}: " + _fmt_times(times))
        for label, need_stable, low_memory in REQUIREMENTS:
            rec = recommend(features, need_stable=need_stable, low_memory=low_memory)["algorithm"]
            allowed = admissible(need_stable, low_memory)
            measured = {a: times[a] for a in allowed if times[a] is not None}
            conflict = rec not in allowed
            rec_time = times[rec]
            if measured:
                fastest = min(measured, key=measured.get)
                ratio = None if rec_time is None else rec_time / measured[fastest]
            else:
                # nur Insertion Sort zulässig, aber wegen zu vieler Inversionen
                # nicht gemessen (tritt nur im Zielkonflikt auf)
                fastest, ratio = "Insertion Sort (nicht gemessen)", None
            rows.append({
                "n": n, "data": kind, "requirements": label,
                "c": round(features["inv_per_nlogn"], 4),
                "recommended": rec, "fastest_admissible": fastest,
                "conflict": int(conflict),
                "hit_strict": int(rec == fastest),
                "hit_tolerant": int(ratio is not None and ratio <= TIE_TOLERANCE),
                "ratio": None if ratio is None else round(ratio, 3),
                **{k: _ms(v) for k, v in times.items()},
            })
    return rows


def summarize_hitrate(rows):
    lines = []
    regular = [r for r in rows if not r["conflict"]]
    conflicts = [r for r in rows if r["conflict"]]

    def quote(sub, key):
        return f"{sum(r[key] for r in sub)}/{len(sub)} ({sum(r[key] for r in sub) / len(sub):.1%})"

    lines.append(f"Testfälle ohne Zielkonflikt: {len(regular)}")
    lines.append(f"  Trefferquote streng:              {quote(regular, 'hit_strict')}")
    lines.append(f"  Trefferquote mit 5 % Toleranz:    {quote(regular, 'hit_tolerant')}")
    ratios = [r["ratio"] for r in regular if r["ratio"] is not None]
    lines.append(f"  Laufzeit Empfehlung / Schnellstes: Median {statistics.median(ratios):.2f}, "
                 f"Maximum {max(ratios):.2f}")
    lines.append("")
    lines.append("Nach Anforderung:")
    for label, _, _ in REQUIREMENTS:
        sub = [r for r in regular if r["requirements"] == label]
        if sub:
            lines.append(f"  {label:<26} streng {quote(sub, 'hit_strict')}, "
                         f"tolerant {quote(sub, 'hit_tolerant')}")
    lines.append("")
    lines.append(f"Zielkonflikt (stabil + Speicher knapp, Empfehlung Merge Sort ist "
                 f"nicht O(1)): {len(conflicts)} Fälle, getrennt ausgewiesen")
    lines.append("")
    misses = [r for r in regular if not r["hit_tolerant"]]
    lines.append(f"Fehlempfehlungen (außerhalb der Toleranz): {len(misses)}")
    for r in sorted(misses, key=lambda r: -(r["ratio"] or 0)):
        lines.append(f"  n = {r['n']:>6}, {r['data']}, {r['requirements']}: empfohlen "
                     f"{r['recommended']}, schnellstes {r['fastest_admissible']}, "
                     f"Faktor {r['ratio']}, c = {r['c']}")
    return lines


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

def _ms(seconds):
    return None if seconds is None else round(seconds * 1000, 5)


def _fmt_times(times):
    return "  ".join(f"{k.split()[0]} {'—' if v is None else f'{v * 1000:9.3f} ms'}"
                     for k, v in times.items())


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


# Farbe, Marker und Linienart je Verfahren: auch im Graustufendruck unterscheidbar
STYLE = {
    "Insertion Sort": dict(color="#2a78d6", marker="o", linestyle="-"),
    "Merge Sort":     dict(color="#eb6834", marker="s", linestyle="--"),
    "Quick Sort":     dict(color="#1baf7a", marker="^", linestyle="-."),
    "Heap Sort":      dict(color="#eda100", marker="D", linestyle=":"),
}


def make_plots(out, scaling, presorted, plot_n):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
    except ImportError:
        print("matplotlib nicht installiert, Diagramme übersprungen "
              "(pip install matplotlib).")
        return

    plt.rcParams.update({
        "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#e3e2dc", "grid.linewidth": 0.6,
        "axes.edgecolor": "#8a897f", "lines.linewidth": 1.6, "lines.markersize": 5,
        "legend.frameon": False,
    })

    def de(x, digits=1):
        return f"{x:.{digits}f}".replace(".", ",")

    # A: Skalierung
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for name in ALGOS:
        pts = [(r["n"], r[name]) for r in scaling if r[name] is not None]
        ax.plot(*zip(*pts), label=name, **STYLE[name])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Anzahl Werte n")
    ax.set_ylabel("Laufzeit in ms (Median)")
    ax.legend()
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"abb_skalierung.{ext}", dpi=200)
    plt.close(fig)

    # B: Vorsortiertheit, ein Teilbild je Art der Unordnung
    kinds = list(DISORDER)
    fig, axes = plt.subplots(1, len(kinds), figsize=(6.6, 3.2), sharey=True)
    for ax, kind in zip(axes, kinds):
        pts = sorted((r for r in presorted if r["disorder"] == kind and r["n"] == plot_n),
                     key=lambda r: r["c"])
        for name in ALGOS:
            xy = [(r["c"], r[name]) for r in pts if r[name] is not None]
            ax.plot(*zip(*xy), label=name, **STYLE[name])
        ax.axvline(INV_THRESHOLD, color="#52514a", linewidth=0.9, linestyle=(0, (4, 3)))
        ax.annotate(f"Schwelle c = {de(INV_THRESHOLD)}", xy=(INV_THRESHOLD, 1),
                    xycoords=("data", "axes fraction"), xytext=(4, -2),
                    textcoords="offset points", va="top", fontsize=8, color="#52514a")
        ax.set_title(kind, fontsize=9)
        ax.set_xlabel("c = Inv / (n · log₂ n)")
    axes[0].set_ylabel(f"Laufzeit in ms (Median), n = {plot_n:,}".replace(",", "."))
    for ax in axes:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    for ext in ("pdf", "png"):
        fig.savefig(out / f"abb_vorsortiertheit.{ext}", dpi=200)
    plt.close(fig)
    print(f"Diagramme gespeichert in {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--quick", action="store_true",
                        help="kleine Größen und wenige Läufe, nur zum Testen")
    parser.add_argument("--out", default=str(ROOT / "benchmarks" / "results"))
    args = parser.parse_args()

    if args.quick:
        runs = 3
        scaling_sizes = [1_000, 2_000, 5_000]
        presorted_sizes = [2_000]
        c_values = [0, 0.25, 0.5, 0.75, 1.0, 1.5]
        hitrate_sizes = [8, 16, 32, 1_000]
    else:
        runs = 9
        scaling_sizes = [1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000]
        presorted_sizes = [1_000, 10_000, 50_000]
        c_values = [0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0]
        hitrate_sizes = [8, 16, 32, 100, 1_000, 10_000, 50_000]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    meta = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor(),
        "seed": SEED, "runs": runs, "quick": args.quick,
        "INV_THRESHOLD": INV_THRESHOLD, "SMALL_N": SMALL_N,
        "INSERTION_INV_LIMIT": INSERTION_INV_LIMIT, "TIE_TOLERANCE": TIE_TOLERANCE,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                   encoding="utf-8")

    started = time.perf_counter()
    print("Experiment A: Skalierung")
    scaling = experiment_scaling(scaling_sizes, runs)
    write_csv(out / "results_skalierung.csv", scaling)

    print("Experiment B: Vorsortiertheit")
    presorted = experiment_presorted(presorted_sizes, c_values, runs)
    write_csv(out / "results_vorsortiertheit.csv", presorted)

    print("Experiment C: Trefferquote")
    hitrate = experiment_hitrate(hitrate_sizes, runs)
    write_csv(out / "results_trefferquote.csv", hitrate)

    summary = [f"Sort Advisor Benchmark, {meta['date']}, Python {meta['python']}, "
               f"{meta['system']} {meta['machine']}, {runs} Läufe je Messung (Median)", ""]
    big = scaling[-1]
    summary.append(f"Bezugsgröße bei n = {big['n']}: sorted() {big[BUILTIN]:.2f} ms, "
                   f"Quick Sort {big['Quick Sort']:.2f} ms "
                   f"(Faktor {big['Quick Sort'] / big[BUILTIN]:.1f})")
    summary.append("")
    summary.append("Gleichstand Insertion Sort gegen das schnellste übrige Verfahren "
                   "(c = Inv / (n · log2 n)):")
    for kind in DISORDER:
        for n in presorted_sizes:
            be = break_even(presorted, kind, n)
            summary.append(f"  {kind:<22} n = {n:>6}: "
                           + ("oberhalb des Messbereichs" if be is None else f"c ≈ {be:.2f}"))
    summary.append("")
    summary += summarize_hitrate(hitrate)
    (out / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print()
    print("\n".join(summary))

    plot_n = 10_000 if 10_000 in presorted_sizes else presorted_sizes[-1]
    make_plots(out, scaling, presorted, plot_n)
    print(f"Fertig nach {time.perf_counter() - started:.0f} s. Ergebnisse in {out}")


if __name__ == "__main__":
    main()
