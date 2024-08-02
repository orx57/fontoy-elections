import pandas as pd
import streamlit as st

import constants

@st.cache_data
def load_data(url):
    data = pd.read_csv(url)
    return data

st.title("Nuances politiques")
    
data = load_data(constants.NUANCES_CSV_URL)
st.dataframe(data, hide_index=True, column_config={'Unnamed: 0': None})
