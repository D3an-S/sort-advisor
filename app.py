import streamlit as st 
import pandas as pd
from analysis import analyze

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

    col = df[column]
    
    null_count = col.isna().sum()
    values = col.dropna().tolist()

    if null_count:
        st.info(f"{null_count} leere Werte ignoriert und beim Sortieren ans Ende gestellt.")

    features = analyze(values)

    st.subheader("Eigenschaften der Daten")
    werte, sortiert, duplikate = st.columns(3)
    werte.metric("Anzahl Werte", features["n"])
    sortiert.metric("Vorsortiert", f"{features['sortedness']:.0%}")
    duplikate.metric("Duplikate", f"{features['duplicate_ratio']:.0%}")
