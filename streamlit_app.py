import altair as alt
import pandas as pd
import requests
import streamlit as st

import constants

# Dictionnaire pour stocker les informations des tours
rounds_info: dict = {}


# Fonction pour charger les données CSV
def load_csv(url):
    return pd.read_csv(url)


# Fonction pour charger les données JSON
def load_json(url):
    response = requests.get(url)
    return response.text


# Fonction pour charger les données Parquet
def load_parquet(url, filters=None):
    return pd.read_parquet(url, filters=filters)


# Dictionnaire des fonctions de chargement
loading_functions = {
    "csv": load_csv,
    "json": load_json,
    "parquet": load_parquet,
}


# Fonction pour charger les données avec mise en cache
@st.cache_data
def load_data(url, data_type, load=False, filters=None):
    if load:
        try:
            return loading_functions[data_type](url, filters)
        except KeyError:
            raise ValueError(f"Type de données non pris en charge : {data_type}")
    else:
        return None


# Fonction pour formater l'élection
def format_election(election_id):
    parts = election_id.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None

    election_dict = constants.ELECTION_DICT
    round_dict = constants.ROUND_DICT

    if len(rounds_info[(year, election)]) == 1:
        return f"{election_dict[election]} {year}"
    else:
        return f"{election_dict[election]} {year} {round_dict.get(str(round), '')}".strip()


# Fonction pour obtenir le tour lié
def get_linked_round(id_election):
    parts = id_election.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None

    if round == "t1" and "t2" in rounds_info.get((year, election), {}):
        return True, False, f"{year}_{election}_t2"
    elif round == "t2" and "t1" in rounds_info.get((year, election), {}):
        return False, True, f"{year}_{election}_t1"
    else:
        return False, False, None


# Application principale
st.title("Fontoy Élections")

data = {
    name: load_data(
        params["url"], params["data_type"], params.get("load", False), params.get("filters")
    )
    for name, params in constants.data_sources.items()
}

for election_id in sorted(
    data["candidats_results"]["id_election"].unique(), reverse=True
):
    parts = election_id.split("_")
    year, election = parts[0], parts[1]
    round = parts[2] if len(parts) > 2 else None
    if (year, election) not in rounds_info:
        rounds_info[(year, election)] = set()
    rounds_info[(year, election)].add(round)

with st.sidebar:
    st.warning(
        """
        L'application est en pleine évolution...
        Attendez-vous à de passionnantes nouveautés très prochainement !
        """,
        icon="⚠️",
    )

    st.markdown("## Sélectionnez une élection")

    st.session_state.election_id = st.selectbox(
        "Faites votre choix",
        sorted(data["candidats_results"]["id_election"].unique(), reverse=True),
        format_func=format_election,
        index=None,
        key="selected_election_id",
        placeholder="Élections disponibles...",
    )

    if st.session_state.election_id:
        st.caption(
            """
            En raison des arrondis à la deuxième décimale,
            la somme des pourcentages peut ne pas être égale à 100%.
            """
        )

if st.session_state.election_id:
    st.subheader(format_election(st.session_state.election_id))
    st.subheader("Participations", divider=True)

    # Filtrer les données pour l'élection sélectionnée
    election_general_data = data["general_results"].loc[
        data["general_results"]["id_election"] == st.session_state.election_id
    ]
    election_candidats_data = data["candidats_results"].loc[
        data["candidats_results"]["id_election"] == st.session_state.election_id
    ]

    # Suppression des colonnes entièrement vides
    election_general_data = election_general_data.dropna(axis="columns", how="all")
    election_candidats_data = election_candidats_data.dropna(axis="columns", how="all")

    is_t1, is_t2, id_election_ot = get_linked_round(st.session_state.election_id)

    def calculate_totals(election_data):
        total_inscrits = (
            election_data["Inscrits"].sum() if "Inscrits" in election_data else None
        )
        total_abstentions = (
            election_data["Abstentions"].sum()
            if "Abstentions" in election_data
            else None
        )
        total_votants = (
            election_data["Votants"].sum() if "Votants" in election_data else None
        )
        total_blancs = (
            election_data["Blancs"].sum() if "Blancs" in election_data else None
        )
        total_nuls = election_data["Nuls"].sum() if "Nuls" in election_data else None
        total_exprimes = (
            election_data["Exprimés"].sum() if "Exprimés" in election_data else None
        )
        return (
            total_inscrits,
            total_abstentions,
            total_votants,
            total_blancs,
            total_nuls,
            total_exprimes,
        )

    if is_t2:
        election_general_data_t1 = data["general_results"].loc[
            data["general_results"]["id_election"] == id_election_ot
        ]

        # Calcul du totaux du tour lié au tour sélectionné
        (
            total_inscrits_t1,
            total_abstentions_t1,
            total_votants_t1,
            total_blancs_t1,
            total_nuls_t1,
            total_exprimes_t1,
        ) = calculate_totals(election_general_data_t1)

    # Calcul du totaux du tour sélectionné
    (
        total_inscrits,
        total_abstentions,
        total_votants,
        total_blancs,
        total_nuls,
        total_exprimes,
    ) = calculate_totals(election_general_data)

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

    def display_metric(column, label, value, delta=None, help=None):
        if delta is not None:
            column.metric(label=label, value=value, delta=delta, help=help)
        else:
            column.metric(label=label, value=value, help=help)

    def display_button(is_t2, id_election_ot):
        def goto_other_tour():
            st.session_state.selected_election_id = id_election_ot

        button_label = "Résultats au 1er tour" if is_t2 else "Résultats au 2nd tour"
        st.button(button_label, on_click=goto_other_tour)

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        display_metric(
            col1,
            "Inscrits",
            total_inscrits,
            int(total_inscrits) - int(total_inscrits_t1) if is_t2 else None,
        )
        display_metric(
            col2,
            "Abstentions",
            total_abstentions,
            int(total_abstentions) - int(total_abstentions_t1) if is_t2 else None,
        )
        display_metric(
            col3,
            "Votants",
            total_votants,
            int(total_votants) - int(total_votants_t1) if is_t2 else None,
            "$Votants = Inscrits - Abstentions$",
        )
        if "Blancs" in (election_general_data_t1 if is_t2 else election_general_data):
            display_metric(
                col1,
                "Blancs",
                int(total_blancs),
                int(total_blancs) - int(total_blancs_t1) if is_t2 else None,
            )
        display_metric(
            col2,
            "Nuls",
            total_nuls,
            int(total_nuls) - int(total_nuls_t1) if is_t2 else None,
        )
        display_metric(
            col3,
            "Exprimés",
            total_exprimes,
            int(total_exprimes) - int(total_exprimes_t1) if is_t2 else None,
            "$Exprimés = Votants - Blancs - Nuls$",
        )

    if is_t2:
        st.info("👆 Les delta par rapport au 1er tour sont affichées.")

    display_button(is_t2, id_election_ot)

    st.subheader("Résultats", divider=True)

    if (
        "Nom" in election_candidats_data.columns
        and "Prénom" in election_candidats_data.columns
    ):
        # Création d'une nouvelle colonne 'Candidat·e'
        election_candidats_data.loc[:, "Candidat·e"] = (
            election_candidats_data["Nom"] + " " + election_candidats_data["Prénom"]
        )
        # Groupement des données par personne
        group_by_person = election_candidats_data.groupby("Candidat·e")
        # Aggrégation des données
        agg_dict = {"Voix": "sum"}
        if "Sexe" in election_candidats_data.columns:
            agg_dict["Sexe"] = "first"
        if "Nuance" in election_candidats_data.columns:
            agg_dict["Nuance"] = "first"
        # Calcul du total de voix par personne
        total_voix_personne = group_by_person.agg(agg_dict)
        # Calcul du pourcentage de voix par rapport au total exprimé
        total_voix_personne["% Voix/Exp"] = (
            total_voix_personne["Voix"] / total_voix_exp * 100
        ).round(2)
        st.write(total_voix_personne.sort_values(by="Voix", ascending=False))

        alt.renderers.set_embed_options(
            format_locale="fr-FR", time_format_locale="fr-FR"
        )

        bars = (
            alt.Chart(
                election_candidats_data,
                title=alt.Title(
                    "Voix par candidat·e et bureau de vote",
                    # subtitle=["A growing share of the state's energy has come from renewable sources"],
                    anchor="start",
                    orient="top",
                    offset=20,
                ),
            )
            .mark_bar(size=20)
            .encode(
                x=alt.X("sum(Voix):Q").stack("zero").title("Voix"),
                y=alt.Y("Candidat·e:N"),
                color=alt.Color(r"Code du b\.vote")
                .title("Code du bureau de vote")
                .legend(orient="bottom"),
            )
            .properties(height=alt.Step(30))
        )
        text = (
            alt.Chart(election_candidats_data)
            .mark_text(dx=-15, dy=3, color="white")
            .encode(
                x=alt.X("voix_sum:Q").stack("zero").title("Voix"),
                y=alt.Y("Candidat·e:N"),
                detail=alt.Detail("Code du b\.vote:N").title("Code du bureau de vote"),
                text=alt.Text("voix_sum:Q").title("Voix"),
                opacity=alt.condition(
                    "datum.voix_sum > 30", alt.value(1), alt.value(0)
                ),
                order=alt.Order("Code du b\.vote").title("Code du bureau de vote"),
            )
            .transform_aggregate(
                voix_sum="sum(Voix)", groupby=[r"Code du b\.vote", "Candidat·e"]
            )
        )

        chart = bars + text

        container = st.container(border=True)

        container.altair_chart(chart, theme="streamlit", use_container_width=True)

        # Création d'un tableau croisé dynamique pour les pourcentages par bureau de vote
        pivot_table = pd.pivot_table(
            election_candidats_data,
            values="Voix",
            index=["Candidat·e"],
            columns=["Code du b.vote"],
            aggfunc="sum",
            fill_value=0,
        )

        # Calcul des pourcentages
        for col in pivot_table.columns:
            pivot_table[col] = (pivot_table[col] / pivot_table[col].sum() * 100).round(
                2
            )

        # Affichage du tableau
        st.subheader("Pourcentage de voix par candidat·e et par bureau de vote")
        st.dataframe(
            pivot_table.style.format("{:.2f}%")
            .highlight_max(axis=0, props="color:black;background-color:#DAF7A6")
            .highlight_max(axis=1, props="color:black;background-color:#90EE90")
            .highlight_max(axis=None, props="color:#FF5733")
        )

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
    """Auteur : Olivier Raggi ([GitHub](https://github.com/orx57)
    & [LinkedIn](https://www.linkedin.com/in/orx57)) · Août 2024
    """
)
