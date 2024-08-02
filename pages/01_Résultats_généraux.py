import pandas as pd
import streamlit as st

import constants

@st.cache_data
def load_data(url):
    sel = [("Code du département", "in", ["57"]), ("Code de la commune", "in", ["226"])]
    data = pd.read_parquet(url, filters=sel)
    return data

st.title("Résultats généraux")
    
data = load_data(constants.GENERAL_RESULTS_PARQUET_URL)

option = st.selectbox(
    'Election :',
    data['id_election'].unique(), index=None,
    placeholder="Choisir une élection")

filtered_df = data[data['id_election'] == option]
filtered_df.dropna(axis='columns', how='all', inplace=True)

st.dataframe(filtered_df, hide_index=True,
             column_config={'id_election': None,
                            'id_brut_miom': None,
                            'Code du département': None,
                            'Libellé du département': None,
                            'Code de la commune': None,
                            'Libellé de la commune': None
                            }
            )
