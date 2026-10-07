import streamlit as st 
import pandas as pd

st.title("Sort Advisor")

st.write("Lade eine CSV Datei hoch & wähle eine Spalte aus. Das Tool liefert dir eine begründete Empfehlung für den besten Sortieralgorithmus. ")

file = st.file_uploader("CSV-Datei" type="csv")

if file is not None: 
    pd.read_csv(file, nrows=100_000)
    st.dataframe(df.head())

    column = st.selectbox("Spalte", df.columns)