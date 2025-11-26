from __future__ import annotations

from typing import Tuple
import numpy as np
import pandas as pd

from .chemins import DATA_DIR


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Charge les 3 fichiers bruts depuis le dossier data/."""
    freq_path = DATA_DIR / "frequentation-totale-mdf-2001-a-2016-data-def9.xlsx"
    entrees_path = DATA_DIR / "ENTREES_ET_CATEGORIES_DE_PUBLIC-2.csv"
    museo_path = DATA_DIR / "museofile (1).csv"  # ton vrai fichier

    print("Chargement des données brutes...")
    freq_raw = pd.read_excel(freq_path)
    ent_raw = pd.read_csv(entrees_path, sep=";")
    museo_raw = pd.read_csv(museo_path, sep="|")

    print(f"  freq_raw shape  : {freq_raw.shape}")
    print(f"  ent_raw shape   : {ent_raw.shape}")
    print(f"  museo_raw shape : {museo_raw.shape}")
    return freq_raw, ent_raw, museo_raw


def build_dim_musees(museo_raw: pd.DataFrame) -> pd.DataFrame:
    """Construit la dimension des musées (Museofile)."""
    musees = museo_raw.copy()

    musees = musees.rename(columns={
        "Identifiant": "id_museofile",
        "Nom_officiel": "nom_officiel",
        "Ville": "ville",
        "Departement": "departement",
        "Region": "region",
        "Categorie": "categorie",
        "Domaine_thematique": "domaine_thematique",
        "Annee_creation": "annee_creation",
        "Coordonnees": "coordonnees",
    })

    # 🔥 SUPPRESSION DES COLONNES TROP LOURDES / INUTILES
    cols_to_drop = [
        "Histoire",
        "Atout",
        "Themes",
        "Artiste",
        "Personnage_phare",
        "Interet"
    ]
    musees = musees.drop(columns=[c for c in cols_to_drop if c in musees.columns], errors="ignore")

    # Séparation lat/lon
    def split_coords(coord_str):
        if pd.isna(coord_str):
            return pd.Series({"latitude": np.nan, "longitude": np.nan})
        try:
            lat_str, lon_str = str(coord_str).split(",")
            return pd.Series({
                "latitude": float(lat_str.strip()),
                "longitude": float(lon_str.strip())
            })
        except Exception:
            return pd.Series({"latitude": np.nan, "longitude": np.nan})

    if "coordonnees" in musees.columns:
        coords = musees["coordonnees"].apply(split_coords)
        musees = pd.concat([musees, coords], axis=1)

    return musees



def build_fact_frequentation(ent_raw: pd.DataFrame) -> pd.DataFrame:
    """Construit la table de fréquentation annuelle (ENTREES...)."""
    freq = ent_raw.copy()

    freq = freq.rename(columns={
        "IDPatrimostat": "id_patrimostat",
        "IDMuseofile": "id_museofile",
    })

    freq["annee"] = freq["annee"].astype(int)

    num_cols = [
        "payant", "gratuit", "total",
        "individuel", "scolaires", "groupes_hors_scolaires",
        "moins_18_ans_hors_scolaires", "_18_25_ans"
    ]
    for col in num_cols:
        if col in freq.columns:
            freq[col] = pd.to_numeric(freq[col], errors="coerce")

    freq["part_gratuit"] = freq["gratuit"] / freq["total"]
    freq["part_scolaires"] = freq["scolaires"] / freq["total"]
    freq["part_individuels"] = freq["individuel"] / freq["total"]

    freq = freq.sort_values(["id_patrimostat", "annee"])
    freq = freq.drop_duplicates(subset=["id_patrimostat", "annee"], keep="first")

    print("\nAperçu fact_frequentation :")
    print(freq[["id_patrimostat", "id_museofile", "annee", "total", "payant", "gratuit"]].head())

    return freq


def build_fact_freq_excel(freq_raw: pd.DataFrame) -> pd.DataFrame:
    """Construit la fréquentation Excel au format long."""
    freq = freq_raw.copy()

    year_cols = [col for col in freq.columns if str(col).isdigit()]
    for col in year_cols:
        freq[col] = pd.to_numeric(freq[col], errors="coerce")

    freq = freq.loc[:, ~freq.columns.str.contains("^Unnamed")]

    freq_long = freq.melt(
        id_vars=["REF DU MUSEE", "NEW REGIONS", "NOM DU MUSEE", "VILLE", "Fréquentation"],
        value_vars=year_cols,
        var_name="annee",
        value_name="total_frequentation"
    )

    freq_long = freq_long.rename(columns={
        "REF DU MUSEE": "id_patrimostat",
        "NEW REGIONS": "region_excel",
        "NOM DU MUSEE": "nom_musee_excel",
        "VILLE": "ville_excel",
        "Fréquentation": "type_frequentation",
    })

    freq_long["annee"] = freq_long["annee"].astype(int)

    print("\nAperçu fact_freq_excel :")
    print(freq_long[["id_patrimostat", "annee", "total_frequentation"]].head())

    return freq_long


def merge_dataset(
    musees: pd.DataFrame,
    fact_freq: pd.DataFrame,
    fact_excel: pd.DataFrame
) -> pd.DataFrame:
    """Fusionne les tables en df_modele (musee x annee)."""
    df_f = fact_freq.copy()

    # On supprime d'éventuelles colonnes region/departement côté fréquentation
    for col in ["region", "Region", "departement", "Departement"]:
        if col in df_f.columns:
            df_f = df_f.drop(columns=[col])

    df = df_f.merge(
        musees[
            [
                "id_museofile", "nom_officiel", "region", "departement",
                "categorie", "domaine_thematique",
                "annee_creation", "latitude", "longitude"
            ]
        ],
        on="id_museofile",
        how="left",
    )

    # Par sécurité si pandas a créé region_x / region_y
    if "region_y" in df.columns:
        df = df.rename(columns={"region_y": "region"})
        df = df.drop(columns=["region_x"], errors="ignore")
    if "departement_y" in df.columns:
        df = df.rename(columns={"departement_y": "departement"})
        df = df.drop(columns=["departement_x"], errors="ignore")

    df = df.merge(
        fact_excel[["id_patrimostat", "annee", "total_frequentation"]],
        on=["id_patrimostat", "annee"],
        how="left",
    )

    print("\nAperçu df_modele (fusion) :")
    print(
        df[
            ["id_patrimostat", "id_museofile", "annee",
             "total", "total_frequentation", "nom_officiel", "region"]
        ].head()
    )
    print(f"\nTaille df_modele : {df.shape}")

    return df


def basic_quality_checks(musees, fact_freq, fact_excel, df_modele):
    """Quelques contrôles qualité simples sur les tables construites."""

    #Nombre de musées et d'années
    n_musees_dim = musees["id_museofile"].nunique()
    n_musees_fact = fact_freq["id_museofile"].nunique()
    n_musees_modele = df_modele["id_museofile"].nunique()
    annees = sorted(df_modele["annee"].unique())

    print(f"Nombre de musées (dim_musees)      : {n_musees_dim}")
    print(f"Nombre de musées (fact_frequent.) : {n_musees_fact}")
    print(f"Nombre de musées (df_modele)      : {n_musees_modele}")
    print(f"Années couvertes dans df_modele   : {annees[0]}–{annees[-1]}")

    #Doublons (id_museofile, annee)
    dup = df_modele.duplicated(subset=["id_museofile", "annee"]).sum()
    print(f"Doublons (id_museofile, annee) : {dup}")
    if dup > 0:
        print("Il y a des doublons musée/année dans df_modele.")

    # 3. Valeurs négatives aberrantes sur 'total'
    if "total" in df_modele.columns:
        neg_total = (df_modele["total"] < 0).sum()
        print(f"Entrées totales négatives : {neg_total}")
        if neg_total > 0:
            print("Certaines lignes ont un total < 0.")

