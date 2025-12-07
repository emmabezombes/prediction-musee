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

    #suppression de la colonne nom_du_musee si doublon 
    if "nom_du_musee" in df.columns:
        df = df.drop(columns=["nom_du_musee"])

    # Imputation simple : si total_frequentation manque, on prend total
    if "total_frequentation" in df.columns and "total" in df.columns:
        df["total_frequentation"] = df["total_frequentation"].fillna(df["total"])
    
    # Âge du musée : on s'assure que annee et annee_creation sont numériques
    if "annee_creation" in df.columns and "annee" in df.columns:
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df["annee_creation"] = pd.to_numeric(df["annee_creation"], errors="coerce")

        df["age_musee"] = df["annee"] - df["annee_creation"]
        
        # On met à NaN les âges négatifs ou aberrants
        df.loc[df["age_musee"] < 0, "age_musee"] = np.nan

        # Vérification des NaN sur age_musee
        nb_nan_age = df["age_musee"].isna().sum()
        print(f"NaN dans age_musee : {nb_nan_age}")

        # Indicateur 
        df["age_musee_missing"] = df["age_musee"].isna().astype(int)

        

    
    # Lags et croissance
    df = df.sort_values(["id_museofile", "annee"])
    if "total" in df.columns:
        df["total_t_1"] = df.groupby("id_museofile")["total"].shift(1)
        df["croissance_total"] = (df["total"] - df["total_t_1"]) / df["total_t_1"]
    
    # Vérification NaN total_t_1
    nb_nan_t1 = df["total_t_1"].isna().sum()
    print(f"NaN dans total_t_1 : {nb_nan_t1}")
    # Vérification NaN sur croissance_total
    nb_nan_croiss = df["croissance_total"].isna().sum()
    print(f"NaN dans croissance_total : {nb_nan_croiss}")

    # Indicateurs
    df["total_t_1_missing"] = df["total_t_1"].isna().astype(int)
    df["croissance_missing"] = df["croissance_total"].isna().astype(int)

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
