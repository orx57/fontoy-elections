"""Constantes nécessaires à l'application"""

# Données des élections agrégées

# Résultats par candidat (format parquet)
CANDIDATS_RESULTS_PARQUET_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/4d3b35f6-0b22-4415-a24c-419a676312e2"
)

# Résultats généraux (format parquet)
GENERAL_RESULTS_PARQUET_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/ff16d511-10c0-405e-9b35-511723948fce"
)

# Dictionnaire des nuances politiques
NUANCES_CSV_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/6fd17a6c-519b-465c-a7fd-ad2955fafc76"
)

# Schéma de données associé au fichier Résultats par candidat
SCHEMA_CANDIDATS_RESULTS_JSON_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/c702d75b-4e7e-43c9-84fa-83220302931d"
)

# Schéma de données associé au fichier Résultats généraux
SCHEMA_GENERAL_RESULTS_JSON_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/ced4d21f-9d17-4224-94c0-d0bf0bc28b1c"
)

# Données des élections agrégées
SOURCES_URL = "https://www.data.gouv.fr/fr/datasets/donnees-des-elections-agregees/"

# Table des bureaux de vote du REU
TABLE_BV_REU_PARQUET_URL = (
    "https://www.data.gouv.fr/fr/datasets/r/6faacf36-1897-43f5-bf39-af8b41a15d26"
)

# Dictionnaire associant les URL à leurs types de données et à leurs filtres
data_sources = {
    "candidats_results": {
        "data_type": "parquet",
        "filters": [
            ("Code du département", "in", ["57"]),
            ("Code de la commune", "in", ["226"]),
        ],
        "url": CANDIDATS_RESULTS_PARQUET_URL,
    },
    "general_results": {
        "data_type": "parquet",
        "filters": [
            ("Code du département", "in", ["57"]),
            ("Code de la commune", "in", ["226"]),
        ],
        "url": GENERAL_RESULTS_PARQUET_URL,
    },
    "nuances": {
        "data_type": "csv",
        "url": NUANCES_CSV_URL,
    },
    "schema_candidats_results": {
        "data_type": "json",
        "url": SCHEMA_CANDIDATS_RESULTS_JSON_URL,
    },
    "schema_general_results": {
        "data_type": "json",
        "url": SCHEMA_GENERAL_RESULTS_JSON_URL,
    },
    "table_bv_reu": {
        "data_type": "parquet",
        "filters": [("code_commune", "in", ["57226"])],
        "url": TABLE_BV_REU_PARQUET_URL,
    },
}
