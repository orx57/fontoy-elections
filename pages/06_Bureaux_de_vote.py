import streamlit as st
import pandas as pd

import constants

@st.cache_data
def load_data(url):
    sel = [("code_commune", "in", ["57226"])]
    data = pd.read_parquet(url, filters=sel)
    return data

def main():
    st.title("Bureaux de vote")
    
    data = load_data(constants.TABLE_BV_REU_PARQUET_URL)
    st.dataframe(data, hide_index=True)

    st.write("Source de données :")
    st.write(constants.SOURCES_URL)

if __name__ == "__main__":
    main()
