import streamlit as st 
import pandas as pd

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


    st.dataframe(df.head())

    column = st.selectbox("Spalte", df.columns)

    col = df[column]
    
    null_count = col.isna().sum()
    values = col.dropna().tolist()

    if null_count:
        st.info(f"{null_count} leere Werte ignoriert und beim Sortieren ans Ende gestellt.")

