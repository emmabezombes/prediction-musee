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
PATH_MUSEOFILE = DATA_DIR / "museofile.csv"

OUTPUT_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# 1. Chargement des données brutes
# -------------------------------------------------------------------

print("Chargement des fichiers...")

freq_raw = pd.read_excel(PATH_FREQ_EXCEL)
ent_raw = pd.read_csv(PATH_ENTREES, sep=";")
museo_raw = pd.read_csv(PATH_MUSEOFILE, sep="|")

print("OK - fichiers chargés.")
print(f"freq_raw shape    : {freq_raw.shape}")
print(f"ent_raw shape     : {ent_raw.shape}")
print(f"museo_raw shape   : {museo_raw.shape}")