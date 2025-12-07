# test.py

from pathlib import Path
import pandas as pd

OUTPUT_DIR = Path("output")


def load_df_modele():
    df_path = OUTPUT_DIR / "df_modele_musees.csv"
    df = pd.read_csv(df_path)
    return df


def test_no_duplicate_museum_year():
    """Il ne doit pas y avoir deux lignes pour un même musée et une même année."""
    df = load_df_modele()
    dup = df.duplicated(subset=["id_museofile", "annee"]).sum()
    assert dup == 0, f"Il y a {dup} doublons (id_museofile, annee)"


def test_reasonable_year_range():
    """Les années doivent rester dans une plage raisonnable (2001–2020 par ex.)."""
    df = load_df_modele()
    an_min, an_max = df["annee"].min(), df["annee"].max()
    assert 1990 < an_min <= 2025, f"Année min étrange : {an_min}"
    assert an_max <= 2030, f"Année max étrange : {an_max}"


def test_columns_exist():
    """Quelques colonnes importantes doivent exister dans le dataset."""
    df = load_df_modele()
    expected_cols = [
        "id_museofile",
        "id_patrimostat",
        "annee",
        "total",
        "nom_officiel",
        "region",
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    assert not missing, f"Colonnes manquantes : {missing}"



