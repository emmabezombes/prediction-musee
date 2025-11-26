# src/cleaning.py

import numpy as np
import pandas as pd


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie df_modele et ajoute des variables dérivées utiles pour la modélisation."""
    df = df.copy()

    num_cols = [
        "total", "payant", "gratuit",
        "individuel", "scolaires", "groupes_hors_scolaires",
        "moins_18_ans_hors_scolaires", "_18_25_ans",
        "total_frequentation"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Imputation simple : si total_frequentation manque, on prend total
    if "total_frequentation" in df.columns and "total" in df.columns:
        df["total_frequentation"] = df["total_frequentation"].fillna(df["total"])

    # Âge du musée
    if "annee_creation" in df.columns:
        df["age_musee"] = df["annee"] - df["annee_creation"]
        df.loc[df["age_musee"] < 0, "age_musee"] = np.nan

    # Lags et croissance
    df = df.sort_values(["id_museofile", "annee"])
    if "total" in df.columns:
        df["total_t_1"] = df.groupby("id_museofile")["total"].shift(1)
        df["croissance_total"] = (df["total"] - df["total_t_1"]) / df["total_t_1"]

    # Indicateur de présence de données Excel
    df["has_excel"] = df["total_frequentation"].notna().astype(int)

    # Musée en Île-de-France ?
    if "region" in df.columns:
        df["region"] = df["region"].astype(str).str.strip()
        df["est_idf"] = (df["region"] == "Île-de-France").astype(int)

    print("\nAperçu df_modele après nettoyage/enrichissement :")
    print(
        df[
            ["id_museofile", "annee", "total",
             "total_frequentation", "age_musee", "croissance_total", "region"]
        ].head()
    )

    return df
