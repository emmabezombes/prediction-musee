
from pathlib import Path

# Dossier racine du projet = dossier parent de src/
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

# On s'assure que le dossier output existe
OUTPUT_DIR.mkdir(exist_ok=True)
