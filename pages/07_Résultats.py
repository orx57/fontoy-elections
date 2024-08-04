import pandas as pd
import requests
import streamlit as st

import constants

rounds_dict = {}

# Cette fonction est utilisée pour charger les données à partir d'une URL spécifique.
# Elle utilise un cache pour éviter de recharger les données à chaque fois que le script est exécuté.
@st.cache_data
def load_data(url, data_type, filters=None):
    ## Chargement des données à partir de l'URL basé sur le type de données
    if data_type == 'csv':
        data = pd.read_csv(url)
    elif data_type == 'json':
        response = requests.get(url)
        data = response.text
    elif data_type == 'parquet':
        data = pd.read_parquet(url, filters=filters)
    else:
        raise ValueError(f"Unsupported data type: {data_type}")

    return data

# Fonction de formatage personnalisée
def format_func(option):
    parts = option.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None
    election_dict = {
        "cant": "Cantonales",
        "dpmt": "Départementales",
        "euro": "Européennes",
        "legi": "Législatives",
        "muni": "Municipales",
        "pres": "Présidentielle",
        "regi": "Régionales"
    }
    round_dict = {"t1": "T1", "t2": "T2"}

    # S'il n'y a qu'un seul tour pour ce type d'élection et cette année, omettre le numéro du tour
    if len(rounds_dict[(year, election)]) == 1:
        return f"{election_dict[election]} {year}"
    else:
        return f"{election_dict[election]} {year} {round_dict.get(round, '')}".strip() 

def main():
    # Titre de l'application Streamlit
    st.title("Résultats par candidats")

    # Define a dictionary mapping URLs to their data types and filters
    data_sources = {
        "general_results": {"url": constants.GENERAL_RESULTS_PARQUET_URL, "data_type": "parquet", "filters": [("Code du département", "in", ["57"]), ("Code de la commune", "in", ["226"])]},
        "candidats_results": {"url": constants.CANDIDATS_RESULTS_PARQUET_URL, "data_type": "parquet", "filters": [("Code du département", "in", ["57"]), ("Code de la commune", "in", ["226"])]},
        "nuances": {"url": constants.NUANCES_CSV_URL, "data_type": "csv"},
        "schema_general_results": {"url": constants.SCHEMA_GENERAL_RESULTS_JSON_URL, "data_type": "json"},
        "schema_candidats_results": {"url": constants.SCHEMA_CANDIDATS_RESULTS_JSON_URL, "data_type": "json"},
        "table_bv_reu": {"url": constants.TABLE_BV_REU_PARQUET_URL, "data_type": "parquet", "filters": [("code_commune", "in", ["57226"])]},
    }

    # Chargement des données
    data = {}
    for name, params in data_sources.items():
        data[name] = load_data(params["url"], params["data_type"], params.get("filters"))
        
    # Mettre à jour le dictionnaire des tours avec le nombre de tours pour chaque type d'élection et chaque année
    for option in sorted(data["candidats_results"]['id_election'].unique(), reverse=True):
        parts = option.split("_")
        year, election = parts[0], parts[1]
        round = parts[2] if len(parts) > 2 else None
        if (year, election) not in rounds_dict:
            rounds_dict[(year, election)] = set()
        rounds_dict[(year, election)].add(round)

    # Création d'une boîte de sélection pour choisir l'élection
    option = st.selectbox(
        'Election :',
        sorted(data["candidats_results"]['id_election'].unique(), reverse=True),
        format_func=format_func,
        index=0,
        placeholder="Choisir une élection")

    # Si une élection est sélectionnée
    if option:
        # Filtrage des données pour l'élection sélectionnée
        filtered_df = data["candidats_results"].loc[data["candidats_results"]['id_election'] == option]
        # Suppression des colonnes entièrement vides
        filtered_df = filtered_df.dropna(axis='columns', how='all')

        # Affichage des données filtrées
        st.dataframe(filtered_df, hide_index=True,
                     column_config={
                         'id_election': None,
                         'id_brut_miom': None,
                         'Code du département': None,
                         'Libellé du département': None,
                         'Code de la commune': None,
                         'Libellé de la commune': None
                     }
                     )
        
        # Calcul du total des voix exprimées
        total_voix_exp = filtered_df["Voix"].sum()
        st.write(f"Total de voix exprimés : {total_voix_exp}")

        # Si la colonne 'Nuance' existe
        if 'Nuance' in filtered_df.columns:
            # Calcul du total de voix pour chaque nuance
            total_voix_nuance = filtered_df.groupby('Nuance')['Voix'].sum()
            st.write("Total de voix pour chaque nuance:")
            st.write(total_voix_nuance)
            # Diagramme à barres du nombre total de votes par nuance
            st.bar_chart(total_voix_nuance)

        # Si les colonnes 'Nom' et 'Prénom' existent
        if 'Nom' in filtered_df.columns and 'Prénom' in filtered_df.columns:
            # Création d'une nouvelle colonne 'Nom Prénom'
            filtered_df.loc[:, 'Nom Prénom'] = filtered_df['Nom'] + " " + filtered_df['Prénom']
            # Groupement des données par personne
            group_by_person = filtered_df.groupby('Nom Prénom')
            # Aggrégation des données
            agg_dict = {'Voix': 'sum'}
            if 'Sexe' in filtered_df.columns:
                agg_dict['Sexe'] = 'first'
            if 'Nuance' in filtered_df.columns:
                agg_dict['Nuance'] = 'first'
            # Calcul du total de voix par personne
            total_voix_personne = group_by_person.agg(agg_dict)
            # Calcul du pourcentage de voix par rapport au total exprimé
            total_voix_personne['% Voix/Exp'] = (total_voix_personne['Voix'] / total_voix_exp * 100).round(2)
            st.write("Total de voix par candidats :")
            st.write(total_voix_personne)
            # Diagramme à barres du nombre total de votes par candidat
            st.bar_chart(total_voix_personne['Voix'])

        # Si la colonne 'Sexe' existe
        if 'Sexe' in filtered_df.columns:
            # Calcul du total de voix pour chaque sexe
            total_voix_sexe = filtered_df.groupby('Sexe')['Voix'].sum()
            st.write("Total de voix pour chaque sexe:")
            st.write(total_voix_sexe)
            # Diagramme à barres du nombre total de votes par sexe
            st.bar_chart(total_voix_sexe)

# Exécution de la fonction principale
if __name__ == "__main__":
    main()
