import streamlit as st 
import pandas as pd
from analysis import analyze
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
        c1, c2, c3 = st.columns(3)
        c1.metric("Anzahl Werte", features["n"])
        c2.metric("Vorsortiert", f"{features['sortedness']:.0%}")
        c3.metric("Duplikate", f"{features['duplicate_ratio']:.0%}")

        # Hier kommt später die Empfehlung aus rules.py hin

        st.divider()
        if st.button("Live-Vergleich starten", icon=":material/timer:"):
            results = {}
            skipped = []
            with st.spinner("Algorithmen laufen..."):
                for name, sort_fn in ALGORITHMS.items():
                    if name == "Insertion Sort" and len(values) > 5000:
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
   