import pandas as pd
import streamlit as st

import constants

@st.cache_data
def load_data(url):
    sel = [("Code du département", "in", ["57"]), ("Code de la commune", "in", ["226"])]
    data = pd.read_parquet(url, filters=sel)
    return data

st.title("Résultats par candidats")

data = load_data(constants.CANDIDATS_RESULTS_PARQUET_URL)
st.dataframe(data, hide_index=True)

st.write("Source de données :")
st.write(constants.SOURCES_URL)
