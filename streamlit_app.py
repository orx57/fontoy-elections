import altair as alt
import pandas as pd
import requests
import streamlit as st

import constants

rounds_dict: dict = {}

# Cette fonction est utilisée pour charger les données à partir d'une URL spécifique
# Utilise un cache pour éviter de recharger les données à chaque fois

# Define the loading functions for each data type


def load_csv(url, filters=None):
    return pd.read_csv(url)


def load_json(url, filters=None):
    response = requests.get(url)
    return response.text


def load_parquet(url, filters=None):
    return pd.read_parquet(url, filters=filters)


# Create a dictionary that maps data types to their respective loading functions
loading_functions = {
    "csv": load_csv,
    "json": load_json,
    "parquet": load_parquet,
}


@st.cache_data
def load_data(url, data_type, filters=None):
    try:
        # Use the dictionary to call the appropriate loading function
        return loading_functions[data_type](url, filters)
    except KeyError:
        # Handle unknown data_type
        raise ValueError(f"Unsupported data type: {data_type}")


# Fonction de formatage du nom des élections


def format_election(election_id):
    parts = election_id.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None

    # Dictionary to map election types to their full names
    election_dict = {
        "cant": "Cantonales",
        "dpmt": "Départementales",
        "euro": "Européennes",
        "legi": "Législatives",
        "muni": "Municipales",
        "pres": "Présidentielle",
        "regi": "Régionales",
    }

    # Dictionary to map round numbers to their full forms
    round_dict = {"t1": "T1", "t2": "T2"}

    # S'il n'y a qu'un seul tour pour ce type d'élection et cette année,
    # omettre le numéro du tour
    if len(rounds_dict[(year, election)]) == 1:
        return f"{election_dict[election]} {year}"
    else:
        return f"{election_dict[election]} {year} {round_dict.get(round, '')}".strip()


def check_previous_round(id_election, rounds_dict):
    parts = id_election.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None

    if round == "t1" and "t2" in rounds_dict.get((year, election), {}):
        return True, False, f"{year}_{election}_t2"
    elif round == "t2" and "t1" in rounds_dict.get((year, election), {}):
        return False, True, f"{year}_{election}_t1"
    else:
        return False, False, None


# Titre de l'application
st.title("Fontoy Élections")

# Chargement des données
data = {}
for name, params in constants.data_sources.items():
    data[name] = load_data(params["url"], params["data_type"], params.get("filters"))

# Mettre à jour le dictionnaire des tours avec le nombre de tours
# pour chaque type d'élection et chaque année
for election_id in sorted(
    data["candidats_results"]["id_election"].unique(), reverse=True
):
    parts = election_id.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None
    if (year, election) not in rounds_dict:
        rounds_dict[(year, election)] = set()
    rounds_dict[(year, election)].add(round)

with st.sidebar:

    st.warning("Application en cours de développement...", icon="⚠️")

    st.markdown("## Sélectionnez une élection")

    # Création d'une boîte de sélection pour choisir l'élection
    st.session_state.election_id = st.selectbox(
        "Faites votre choix",
        sorted(data["candidats_results"]["id_election"].unique(), reverse=True),
        format_func=format_election,
        index=None,
        key='selected_election_id',
        placeholder="Élections disponibles...",
    )

    if st.session_state.election_id:
        st.caption("En raison des arrondis à la deuxième décimale, la somme des pourcentages peut ne pas être égale à 100%.")

# Si une élection est sélectionnée
if st.session_state.election_id:

    st.subheader(format_election(st.session_state.election_id))
    st.subheader("Participations", divider=True)

    if st.session_state.election_id:
        # Filtrage des données pour l'élection sélectionnée
        election_general_data = data["general_results"].loc[
            data["general_results"]["id_election"] == st.session_state.election_id
        ]
        election_candidats_data = data["candidats_results"].loc[
            data["candidats_results"]["id_election"] == st.session_state.election_id
        ]
        # Suppression des colonnes entièrement vides
        election_general_data = election_general_data.dropna(axis="columns", how="all")
        election_candidats_data = election_candidats_data.dropna(
            axis="columns", how="all"
        )

        is_t1, is_t2, id_election_ot = check_previous_round(
            st.session_state.election_id, rounds_dict
        )
        if is_t2:
            election_general_data_t1 = data["general_results"].loc[
                data["general_results"]["id_election"] == id_election_ot
            ]
            total_inscrits_t1 = election_general_data_t1["Inscrits"].sum()
            total_abstentions_t1 = election_general_data_t1["Abstentions"].sum()
            total_votants_t1 = election_general_data_t1["Votants"].sum()
            if "Blancs" in election_general_data_t1:
                total_blancs_t1 = election_general_data_t1["Blancs"].sum()
            total_nuls_t1 = election_general_data_t1["Nuls"].sum()
            total_exprimes_t1 = election_general_data_t1["Exprimés"].sum()

        # Calcul du totaux
        total_inscrits = election_general_data["Inscrits"].sum()
        total_abstentions = election_general_data["Abstentions"].sum()
        total_votants = election_general_data["Votants"].sum()
        if "Blancs" in election_general_data:
            total_blancs = election_general_data["Blancs"].sum()
        total_nuls = election_general_data["Nuls"].sum()
        total_exprimes = election_general_data["Exprimés"].sum()

        total_voix_exp = election_candidats_data["Voix"].sum()

        # Vérifications
        if total_voix_exp != total_exprimes:
            st.warning(
                """
                Attention :
                le total des voix exprimés n'est pas égale au des bulletins exprimés !
                """,
                icon="⚠️",
            )

        if is_t2:
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label="Inscrits",
                        value=(total_inscrits),
                        delta=(int(total_inscrits) - int(total_inscrits_t1)),
                    )
                with col2:
                    st.metric(
                        label="Abstentions",
                        value=(total_abstentions),
                        delta=(int(total_abstentions) - int(total_abstentions_t1)),
                    )
                with col3:
                    st.metric(
                        label="Votants",
                        value=(total_votants),
                        delta=(int(total_votants) - int(total_votants_t1)),
                        help="$Votants = Inscrits - Abstentions$",
                    )
                if "Blancs" in election_general_data_t1:
                    with col1:
                        st.metric(
                            label="Blancs",
                            value=(int(total_blancs)),
                            delta=(int(total_blancs) - int(total_blancs_t1)),
                        )
                with col2:
                    st.metric(
                        label="Nuls",
                        value=(total_nuls),
                        delta=(int(total_nuls) - int(total_nuls_t1)),
                    )
                with col3:
                    st.metric(
                        label="Exprimés",
                        value=(total_exprimes),
                        delta=(int(total_exprimes) - int(total_exprimes_t1)),
                        help="$Exprimés = Votants - Blancs - Nuls$",
                    )
        else:
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label="Inscrits",
                        value=(total_inscrits),
                    )
                with col2:
                    st.metric(
                        label="Abstentions",
                        value=(total_abstentions),
                    )
                with col3:
                    st.metric(
                        label="Votants",
                        value=(total_votants),
                        help="$Votants = Inscrits - Abstentions$",
                    )
                if "Blancs" in election_general_data:
                    with col1:
                        st.metric(
                            label="Blancs",
                            value=(int(total_blancs)),
                        )
                with col2:
                    st.metric(
                        label="Nuls",
                        value=(total_nuls),
                    )
                with col3:
                    st.metric(
                        label="Exprimés",
                        value=(total_exprimes),
                        help="$Exprimés = Votants - Blancs - Nuls$",

                    )

        if is_t2:
            st.info("👆 Les delta par rapport au 1er tour sont affichées.")
            def goto_t1():
                st.session_state.selected_election_id = id_election_ot
            st.button('Résultats au 1er tour', on_click=goto_t1)
        elif is_t1:
            def goto_t2():
                st.session_state.selected_election_id = id_election_ot
            st.button('Résultats au 2nd tour', on_click=goto_t2)

        # base = alt.Chart(election_general_data).encode(
        #     theta=alt.Theta(field="Inscrits", stack=True, type="quantitative"),
        #     color=alt.Color(
        #         field=r"Code du b\.vote", type="nominal", title="Bureau de vote"
        #     ),
        # )

        # pie = base.mark_arc(innerRadius=80)
        # text = base.mark_text(radius=60, size=12).encode(text="Inscrits")

        # chart = pie + text

        # st.altair_chart(chart, theme="streamlit", use_container_width=True)

        # nchart = (
        #     alt.Chart(election_general_data)
        #     .transform_joinaggregate(
        #         TotalInscrits="sum(Inscrits)",
        #     )
        #     .transform_calculate(PercentOfTotal="datum.Inscrits / datum.TotalInscrits")
        #     .mark_bar()
        #     .encode(
        #         alt.X("PercentOfTotal:Q", axis=alt.Axis(format=".0%")),
        #         y=r"Code du b\.vote:N",
        #     )
        # )

        # st.altair_chart(nchart, theme="streamlit", use_container_width=True)

        # # Affichage des données filtrées

        # st.dataframe(
        #     election_general_data,
        #     hide_index=True,
        #     column_config={
        #         "id_election": None,
        #         "id_brut_miom": None,
        #         "Code du département": None,
        #         "Libellé du département": None,
        #         "Code de la commune": None,
        #         "Libellé de la commune": None,
        #     },
        # )

        # st.dataframe(
        #     election_candidats_data,
        #     hide_index=True,
        #     column_config={
        #         "id_election": None,
        #         "id_brut_miom": None,
        #         "Code du département": None,
        #         "Libellé du département": None,
        #         "Code de la commune": None,
        #         "Libellé de la commune": None,
        #     },
        # )

        # # Si la colonne 'Nuance' existe
        # if "Nuance" in election_candidats_data.columns:
        #     # Calcul du total de voix pour chaque nuance
        #     total_voix_nuance = election_candidats_data.groupby("Nuance")["Voix"].sum()
        #     st.write("Total de voix pour chaque nuance:")
        #     st.write(total_voix_nuance)
        #     # Diagramme à barres du nombre total de votes par nuance
        #     st.bar_chart(total_voix_nuance)

        # # Si les colonnes 'Nom' et 'Prénom' existent
        # if (
        #     "Nom" in election_candidats_data.columns
        #     and "Prénom" in election_candidats_data.columns
        # ):
        #     # Création d'une nouvelle colonne 'Nom Prénom'
        #     election_candidats_data.loc[:, "Nom Prénom"] = (
        #         election_candidats_data["Nom"] + " " + election_candidats_data["Prénom"]
        #     )
        #     # Groupement des données par personne
        #     group_by_person = election_candidats_data.groupby("Nom Prénom")
        #     # Aggrégation des données
        #     agg_dict = {"Voix": "sum"}
        #     if "Sexe" in election_candidats_data.columns:
        #         agg_dict["Sexe"] = "first"
        #     if "Nuance" in election_candidats_data.columns:
        #         agg_dict["Nuance"] = "first"
        #     # Calcul du total de voix par personne
        #     total_voix_personne = group_by_person.agg(agg_dict)
        #     # Calcul du pourcentage de voix par rapport au total exprimé
        #     total_voix_personne["% Voix/Exp"] = (
        #         total_voix_personne["Voix"] / total_voix_exp * 100
        #     ).round(2)
        #     st.write("Total de voix par candidats :")
        #     st.write(total_voix_personne)
        #     # Diagramme à barres du nombre total de votes par candidat
        #     st.bar_chart(total_voix_personne["Voix"])

        # # Si la colonne 'Sexe' existe
        # if "Sexe" in election_candidats_data.columns:
        #     # Calcul du total de voix pour chaque sexe
        #     total_voix_sexe = election_candidats_data.groupby("Sexe")["Voix"].sum()
        #     st.write("Total de voix pour chaque sexe:")
        #     st.write(total_voix_sexe)
        #     # Diagramme à barres du nombre total de votes par sexe
        #     st.bar_chart(total_voix_sexe)

        # st.markdown(
        #     """
        #     Résultats du 2e tour des #Législatives2024 à Fontoy :
        #     - Le taux de participation a atteint 60.11 %, ce qui représente
        #     une augmentation de 38 voix par rapport au 1er tour (58.51 %).
        #     - Laurent Jacobelli (RN) a gagné 93 voix supplémentaires,
        #     soit une augmentation de 13.96 % entre les deux tours.
        #     319 voix de plus qu'en 2022.
        #     - Céline Leger (UG) a gagné 212 voix supplémentaires,
        #     soit une augmentation de 72.60 % entre les deux tours.
        #     174 voix de plus qu'en 2022.
        #     - La différence entre les deux candidats est de 255 voix.
        #     - Les bulletins blancs augmentent de 268.75 % entre les deux tours,
        #     de 32 à 118.
        #     - Les bulletins nuls progressent de 214.29 % entre les deux tours,
        #     de 7 à 22.
        #     """
        # )

else:

    st.info(
        """
        ### 📢 Aucune élection n'est sélectionnée !
        Pour afficher les informations et les données d'une élection,
        commencez par **sélectionner une élection**.

        Pour cela, **faites votre choix** dans le **menu
        latéral** parmi les **élections disponibles**.
    """
    )

st.subheader("A propos de l'application", divider=True)

st.markdown(
    """
    Cette application permet d'afficher les **données publiques des élections
    pour Fontoy** à partir des API de data.gouv.fr.
    """
)

st.caption(
    """
    Auteur : Olivier Raggi ([GitHub](https://github.com/orx57) &
        [LinkedIn](https://www.linkedin.com/in/orx57))
        · Août 2024
    """
)
