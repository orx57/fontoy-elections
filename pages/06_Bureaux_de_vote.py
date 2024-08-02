import streamlit as st
import pandas as pd

import constants

@st.cache_data
def load_data(url):
    sel = [("code_commune", "in", ["57226"])]
    data = pd.read_parquet(url, filters=sel)
    return data

st.title("Bureaux de vote")


data = load_data(constants.TABLE_BV_REU_PARQUET_URL)

option = st.selectbox(
    'Numéro du bureau de vote :',
    sorted(data['code'].unique()), index=None,
    placeholder="Choisir un numéro de bureau de vote")

filtered_df = data[data['code'] == option]
filtered_df = filtered_df.dropna(axis='columns', how='all')

if option:
    st.dataframe(filtered_df, hide_index=True)
