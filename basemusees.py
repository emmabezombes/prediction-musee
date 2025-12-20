from src.chemins import OUTPUT_DIR
from src.build_bases import (
    load_raw_data,
    build_dim_musees,
    build_fact_frequentation,
    build_fact_freq_excel,
    merge_dataset,
    basic_quality_checks,
)
from src.cleaning import clean_and_enrich


def main():
    #Chargement
    freq_raw, ent_raw, museo_raw = load_raw_data()

    #Construction des tables
    musees = build_dim_musees(museo_raw)
    fact_freq = build_fact_frequentation(ent_raw)
    fact_excel = build_fact_freq_excel(freq_raw)

    #Fusion
    df_modele = merge_dataset(musees, fact_freq, fact_excel)

    #Nettoyage + enrichissement
    df_modele_clean = clean_and_enrich(df_modele)

    #Export
    OUTPUT_DIR.mkdir(exist_ok=True)
    musees.to_csv(OUTPUT_DIR / "musees.csv", index=False)
    fact_freq.to_csv(OUTPUT_DIR / "frequentation_annuelle.csv", index=False)
    fact_excel.to_csv(OUTPUT_DIR / "frequentation_excel_long.csv", index=False)
    df_modele_clean.to_csv(OUTPUT_DIR / "df_modele_musees.csv", index=False)

    print(f"\nFichiers sauvegardés dans : {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()

