import streamlit as st
import pandas as pd

import constants

def load_data(url):
    data = pd.read_csv(url)
    return data

st.title("Nuances politiques")
    
data = load_data(constants.NUANCES_CSV_URL)
st.dataframe(data, column_config={'Unnamed: 0': None})

st.write("Source de données :")
st.write(constants.SOURCES_URL)
