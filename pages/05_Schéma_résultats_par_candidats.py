import requests
import streamlit as st
import pandas as pd

import constants

@st.cache_data
def load_data(url):
    response = requests.get(url)
    return response.text

def main():
    st.title("Schéma des résultats par candidats")
    
    data = load_data(constants.SCHEMA_CANDIDATS_RESULTS_JSON_URL)
    st.json(data)

    st.write("Source de données :")
    st.write(constants.SOURCES_URL)
    
if __name__ == "__main__":
    main()
