import streamlit as st
import pandas as pd

import constants

@st.cache_data
def load_data(url):
    sel = [("Code du département", "in", ["57"]), ("Code de la commune", "in", ["226"])]
    data = pd.read_parquet(url, filters=sel)
    return data

def main():
    st.title("Résultats généraux")
    
    data = load_data(constants.GENERAL_RESULTS_PARQUET_URL)
    st.dataframe(data, hide_index=True)

    st.write("Source de données :")
    st.write(constants.SOURCES_URL)

if __name__ == "__main__":
    main()
