import streamlit as st 
import pandas as pd
from analysis import analyze
from rules import recommend, INV_THRESHOLD
import time
from sorting import ALGORITHMS

st.set_page_config(page_title="Sort Advisor", page_icon=":material/filter_list:", layout="wide")

st.title("Sort Advisor")

st.write("Lade eine CSV Datei hoch & wähle eine Spalte aus. Das Tool liefert dir eine begründete Empfehlung für den besten Sortieralgorithmus. ")

file = st.file_uploader("CSV-Datei", type="csv")

if file is not None: 
    try:
        df = pd.read_csv(file, nrows=100_000)
    except Exception:
        st.error("Die Datei konnte nicht als CSV gelesen werden.")
        st.stop()

    if df.empty:
        st.warning("Die Datei enthält keine Daten.")
        st.stop()

    with st.expander("Datenvorschau"):
        st.dataframe(df.head())

    column = st.selectbox("Spalte", df.columns)


    options = st.pills("Anforderungen an den Algortihmus", ["Stabilität notwendig", "Speicher knapp"], selection_mode="multi")
    need_stable = "Stabilität notwendig" in options
    low_memory = "Speicher knapp" in options

    col = df[column]
    
    null_count = col.isna().sum()
    values = col.dropna().tolist()

    if null_count:
        st.info(f"{null_count} leere Werte ignoriert und beim Sortieren ans Ende gestellt.")

    if st.button("Analyse starten", type="primary", icon=":material/play_arrow:"):
        st.session_state.analyzed_column = column

    if st.session_state.get("analyzed_column") == column:
        with st.spinner("Analyse läuft..."):
            features = analyze(values)
        st.success("Analyse abgeschlossen!")

        st.subheader("Eigenschaften der Daten")
        def pct(x):
            return "–" if x is None else f"{x:.0%}"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Anzahl Werte", f"{features['n']:,}".replace(",", "."))
        c2.metric("Vorsortiert", pct(features["sortedness"]),
                  help="Anteil der Nachbarpaare in richtiger Reihenfolge. "
                       f"Entspricht {features['runs']} aufsteigenden Runs.")
        c3.metric("Inversionen", pct(features["inversion_ratio"]),
                  help="Anteil falsch geordneter Paare (0 % = sortiert, 100 % = umgekehrt). "
                       "Insertion Sort braucht genau so viele Verschiebungen, wie es Inversionen gibt.")
        c4.metric("Duplikate", pct(features["duplicate_ratio"]))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Datentyp", "Zahl" if features["is_numeric"]
                  else "Text" if features["is_comparable"] else "gemischt")
        c2.metric("Runs", "–" if features["runs"] is None
                  else f"{features['runs']:,}".replace(",", "."),
                  help="Anzahl aufsteigender Teilstücke (Mannila 1985). "
                       "1 = komplett sortiert. Lässt sich aus „Vorsortiert“ umrechnen: "
                       "Runs = (n − 1) · (1 − Vorsortiert) + 1.")
        c3.metric("Inversionen absolut", "–" if features["inversions"] is None
                  else f"{features['inversions']:,}".replace(",", "."),
                  help="Anzahl Paare, die falsch herum stehen. "
                       "Entspricht genau der Zahl der Verschiebungen bei Insertion Sort.")
        c4.metric("Inv / (n · log₂ n)", "–" if features["inv_per_nlogn"] is None
                  else f"{features['inv_per_nlogn']:.2f}".replace(".", ","),
                  help=f"Entscheidet über die Insertion-Regel: bis {INV_THRESHOLD} "
                       f"(gemessene Schwelle) wird Insertion Sort empfohlen.")

        st.subheader("Empfehlung")
        rec = recommend(features, need_stable=need_stable, low_memory=low_memory)
        if rec["algorithm"] is None:
            st.warning(rec["reasons"][0])
        else:
            st.success(f"**{rec['algorithm']}**")
            for reason in rec["reasons"]:
                st.write(reason)
            for note in rec["notes"]:
                st.caption(note)

        st.divider()
        if st.button("Live-Vergleich starten", icon=":material/timer:"):
            results = {}
            skipped = []
            with st.spinner("Algorithmen laufen..."):
                for name, sort_fn in ALGORITHMS.items():
                    # Insertion nur überspringen, wenn es nicht empfohlen ist,
                    # sonst ließe sich die Empfehlung nicht überprüfen
                    if (name == "Insertion Sort" and len(values) > 5000
                            and rec["algorithm"] != "Insertion Sort"):
                        skipped.append(name)
                        continue
                    start = time.perf_counter()
                    sort_fn(values)
                    results[name] = (time.perf_counter() - start) * 1000

            st.subheader("Laufzeit in Millisekunden")
            st.bar_chart(pd.Series(results))
            fastest = min(results, key=results.get)
            st.write(f"Am schnellsten: **{fastest}** ({results[fastest]:.1f} ms)")
            if skipped:
                st.caption(f"{', '.join(skipped)} übersprungen: bei mehr als 5.000 Werten zu langsam (O(n²)).")
   