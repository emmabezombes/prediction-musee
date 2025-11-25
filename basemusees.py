import pandas as pd
import numpy as np
from pathlib import Path

# -------------------------------------------------------------------
# 0. Configuration des chemins
# -------------------------------------------------------------------

# Dossier racine = dossier où se trouve ce script
ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

PATH_FREQ_EXCEL = DATA_DIR / "frequentation-totale-mdf-2001-a-2016-data-def9.xlsx"
PATH_ENTREES = DATA_DIR / "ENTREES_ET_CATEGORIES_DE_PUBLIC-2.csv"
PATH_MUSEOFILE = DATA_DIR / "museofile (1).csv"

OUTPUT_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# 1. Chargement des données brutes
# -------------------------------------------------------------------
freq_raw = pd.read_excel(PATH_FREQ_EXCEL)
ent_raw = pd.read_csv(PATH_ENTREES, sep=";")
museo_raw = pd.read_csv(PATH_MUSEOFILE, sep="|")

print("OK - fichiers chargés.")
print(f"freq_raw shape    : {freq_raw.shape}")
print(f"ent_raw shape     : {ent_raw.shape}")
print(f"museo_raw shape   : {museo_raw.shape}")


# -------------------------------------------------------------------
# 2. Table musees (à partir de museofile)
# -------------------------------------------------------------------

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
    "Coordonnees": "coordonnees"
})

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

coords = musees["coordonnees"].apply(split_coords)
musees = pd.concat([musees, coords], axis=1)


print("Aperçu musees :")
print(musees[["id_museofile", "nom_officiel", "region"]].head())


# -------------------------------------------------------------------
# 3. Table frequentation_annuelle (ENTREES_ET_CATEGORIES_DE_PUBLIC)
# -------------------------------------------------------------------
frequentation = ent_raw.copy()

frequentation = frequentation.rename(columns={
    "IDPatrimostat": "id_patrimostat",
    "IDMuseofile": "id_museofile"
})

frequentation["annee"] = frequentation["annee"].astype(int)

for col in [
    "payant", "gratuit", "total",
    "individuel", "scolaires", "groupes_hors_scolaires",
    "moins_18_ans_hors_scolaires", "_18_25_ans"
]:
    if col in frequentation.columns:
        frequentation[col] = pd.to_numeric(frequentation[col], errors="coerce")

frequentation["part_gratuit"] = frequentation["gratuit"] / frequentation["total"]
frequentation["part_scolaires"] = frequentation["scolaires"] / frequentation["total"]
frequentation["part_individuels"] = frequentation["individuel"] / frequentation["total"]

frequentation = frequentation.sort_values(["id_patrimostat", "annee"])
frequentation = frequentation.drop_duplicates(
    subset=["id_patrimostat", "annee"], keep="first"
)

print("Aperçu frequentation_annuelle :")
print(
    frequentation[
        ["id_patrimostat", "id_museofile", "annee", "total", "payant", "gratuit"]
    ].head()
)

# -------------------------------------------------------------------
# 4. Table freq_long depuis l'Excel 2001-2016
# -------------------------------------------------------------------
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
    "Fréquentation": "type_frequentation"
})

freq_long["annee"] = freq_long["annee"].astype(int)

print("Aperçu freq_long :")
print(
    freq_long[["id_patrimostat", "annee", "total_frequentation"]].head()
)

# -------------------------------------------------------------------
# 5. Table finale df_modele
# -------------------------------------------------------------------
df_modele = frequentation.merge(
    musees[
        [
            "id_museofile", "nom_officiel", "region", "departement",
            "categorie", "domaine_thematique",
            "annee_creation", "latitude", "longitude"
        ]
    ],
    on="id_museofile",
    how="left"
)

df_modele = df_modele.merge(
    freq_long[["id_patrimostat", "annee", "total_frequentation"]],
    on=["id_patrimostat", "annee"],
    how="left"
)

print("Colonnes df_modele :")
print(df_modele.columns.tolist())

print("Colonnes liées à la région dans df_modele :")
print([c for c in df_modele.columns if "region" in c.lower()])

print("Aperçu df_modele :")
print(
    df_modele[
        ["id_patrimostat", "id_museofile", "annee",
         "total", "total_frequentation", "nom_officiel", "region"]
    ].head()
)

print(f"\nTaille finale df_modele : {df_modele.shape}")


