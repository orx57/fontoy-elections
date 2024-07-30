import requests
import streamlit as st

import constants

@st.cache_data
def load_data(url):
    response = requests.get(url)
    return response.text

st.title("Schéma des résultats généraux")

data = load_data(constants.SCHEMA_GENERAL_RESULTS_JSON_URL)
st.json(data)

st.write("Source de données :")
st.write(constants.SOURCES_URL)
