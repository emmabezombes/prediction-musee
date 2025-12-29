import numpy as np
import pandas as pd

def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie df_modele et ajoute des variables dérivées utiles pour la modélisation."""
    df = df.copy()

    # ==============================================================================
    # 1. TYPAGE ET NETTOYAGE DE BASE
    # ==============================================================================
    num_cols = [
        "total", "payant", "gratuit",
        "individuel", "scolaires", "groupes_hors_scolaires",
        "moins_18_ans_hors_scolaires", "_18_25_ans",
        "total_frequentation"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Suppression de la colonne nom_officiel si doublon 
    if "nom_du_musee" in df.columns:
        df = df.drop(columns=["nom_du_musee"])

    # Imputation simple : si total manque, on prend total_frequentation (Excel)
    if "total_frequentation" in df.columns and "total" in df.columns:
        df["total"] = df["total"].fillna(df["total_frequentation"])
        # Indicateur de présence de données Excel
        df["has_excel"] = df["total_frequentation"].notna().astype(int)
    
    # ==============================================================================
    # 2. CALCULS TEMPORELS (ÂGE, LAGS, CROISSANCE)
    # ==============================================================================
    # Âge du musée
    if "annee_creation" in df.columns and "annee" in df.columns:
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df["annee_creation"] = pd.to_numeric(df["annee_creation"], errors="coerce")

        df["age_musee"] = df["annee"] - df["annee_creation"]
        
        # On met à NaN les âges négatifs ou aberrants
        df.loc[df["age_musee"] < 0, "age_musee"] = np.nan
        
        # Indicateur 
        df["age_musee_missing"] = df["age_musee"].isna().astype(int)

    # Lags (Année précédente)
    df_lag = df[["id_museofile", "annee", "total"]].copy()
    df_lag["annee"] = df_lag["annee"] + 1 
    df_lag = df_lag.rename(columns={"total": "total_t_1"})
    
    df = df.merge(df_lag, on=["id_museofile", "annee"], how="left")

    # Calcul de la croissance
    df["croissance_total"] = np.where(
        (df["total_t_1"] > 0) & (df["total_t_1"].notna()),
        (df["total"] - df["total_t_1"]) / df["total_t_1"],
        np.nan
    )
    df["croissance_total"] = df["croissance_total"].replace([np.inf, -np.inf], np.nan)

    # ==============================================================================
    # 3. GESTION INTELLIGENTE DES DOMAINES (Multi-label)
    # ==============================================================================
    if "domaine_thematique" in df.columns:
        print("Traitement des domaines thématiques...")
        
        def clean_text_domain(x):
            if pd.isna(x): return None
            x = str(x).lower().strip().rstrip(".")
            # Uniformisation des séparateurs
            x = x.replace(";", "/").replace(",", "/").replace("|", "/").replace(".", " /")
            x = " ".join(x.split())
            return x

        # Nettoyage et transformation en liste
        df["domaine_clean"] = df["domaine_thematique"].apply(clean_text_domain)
        df["domaine_list"] = df["domaine_clean"].apply(lambda x: x.split("/") if pd.notna(x) else [])

        # Identification des Top Domaines (> 50 occurrences)
        all_domaines = df["domaine_list"].explode().str.strip()
        compte_domaines = all_domaines.value_counts()
        SEUIL_DOMAINE = 50
        domaines_a_garder = compte_domaines[compte_domaines > SEUIL_DOMAINE].index.tolist()

        # Création des colonnes binaires (is_beaux_arts, is_histoire...)
        for dom in domaines_a_garder:
            if pd.isna(dom) or dom == "": continue
            
            # Nom de colonne propre (ex: "beaux-arts" -> "is_beaux_arts")
            col_name = f"is_{dom.replace(' ', '_').replace('-', '_')}"
            
            # 1 si présent, 0 sinon
            df[col_name] = df["domaine_list"].apply(
                lambda liste: 1 if dom in [x.strip() for x in liste] else 0
            )
            
        # Nettoyage intermédiaire (optionnel, on peut garder pour verif)
        # df = df.drop(columns=["domaine_clean", "domaine_list"])

    # ==============================================================================
    # 4. AUTRES VARIABLES
    # ==============================================================================
    # Musée en Île-de-France ?
    if "region" in df.columns:
        df["region"] = df["region"].astype(str).str.strip()
        df["est_idf"] = (df["region"] == "Île-de-France").astype(int)

    print("\nAperçu df_modele après nettoyage/enrichissement :")
    cols_view = ["id_museofile", "annee", "total", "total_frequentation", "age_musee"]
    # On ajoute quelques colonnes domaines si elles existent pour vérifier
    cols_dom = [c for c in df.columns if c.startswith("is_")][:2]
    print(df[cols_view + cols_dom].head())

    
    # ==============================================================================
    # 4. NETTOYAGE DES CATÉGORIES (Utilisation de votre Mapping)
    # ==============================================================================
    if "categorie" in df.columns:
        print("Nettoyage des catégories...")

        # 1. Fonction de nettoyage texte simple
        def clean_cat_text(x):
            if pd.isna(x): return "Autre"
            x = str(x).lower().strip().rstrip(".")
            x = x.replace(";", "/").replace(",", "/").replace("|", "/").replace(".", " /")
            x = " ".join(x.split())
            return x

        df["categorie"] = df["categorie"].apply(clean_cat_text)

        # 2. Votre dictionnaire de regroupement (C'est le cœur du nettoyage)
        map_cat = {
            "ecomusée": "écomusée",
            "maison d'artiste": "maison musée",
            "maison d'illustre": "maison musée",
            "maison des illustres": "maison musée",
            "musée en zone rurale": "musée en milieu rural",
            "musée de site : site archéologique": "musée de site",
            "musée de site : carreau de mine": "musée de site",
            "architecture contemporaine remarquable (extension)": "architecture contemporaine remarquable",
            "musée de site : usine": "musée de site",
            "musée de site / musée en milieu rural" : "musée en milieu rural",
            "écomusée / musée en milieu rural": "musée en milieu rural",
            "écomusée / musée en zone rurale": "musée en milieu rural",
            "musée de site / musée en zone rurale" : " musée en milieu rural",
            "maison musée / maison des illustres" : "maison musée",
            "musée littéraire / musée en milieu rural": "musée en milieu rural",
            "musée de site / jardin remarquable": "jardin remarquable",
            "domaine national / jardin remarquable": "jardin remarquable",
            "maison des illustres / musée en milieu rural": "musée en milieu rural",
            "maison musée / maison des illustres / musée en milieu rural": "musée en milieu rural",
            "musée de plein air / musée en milieu rural": "musée en milieu rural",
            "musée de site / architecture contemporaine remarquable": "architecture contemporaine remarquable",
            "musée d'art sacré / musée en milieu rural": "musée en milieu rural",
            "musée de site / maison d'artiste" : "maison musée",
            "musée de site / maison des illustres" : "maison musée",
            "musée de site / site archéologique / musée en milieu rural": "musée en milieu rural",
            "ecomusée / musée de plein air / musée de site" : "écomusée",
            "musée de site / musée en zone rurale / site archéologique" : "musée en milieu rural",
            "ecomusée / musée de plein air" : "écomusée", 
            "ecomusée / musée de site" : "écomusée",
            "musée de site / maison musée / maison des illustres" : "maison musée",
            "musée de site / musée littéraire" : "musée littéraire",
            "musée de site / domaine national": "domaine national",
            "écomusée / musée de site / musée en zone rurale" : "musée en milieu rural",
            "architecture contemporaine remarquable / musée en milieu rural" :"musée en milieu rural",
            "musée de plein air / musée de site":"musée de site",
            "musée de plein air / maison musée / maison des illustres / musée en milieu rural" : "musée en milieu rural",
            "écomusée / musée de plein air / musée de site / musée en milieu rural" :"musée en milieu rural",
            "musée de plein air / musée de site / musée en zone rurale":"musée en milieu rural",
            "musée de site / musée littéraire / maison des illustres (2017)": "maison musée littéraire",
            "musée littéraire / architecture contemporaine remarquable": "musée littéraire",
            "musée de site / musée littéraire / maison des illustres / musée en milieu rural" : "musée en milieu rural",
            "musée de site / maison musée / musée littéraire / maison des illustres / musée en zone rurale": "musée en milieu rural",
            "maison musée / maison d'artiste / musée littéraire" : "maison musée littéraire",
            "écomusée / musée de site / musée en milieu rural" : "musée en milieu rural",
            "écomusée / musée de plein air / musée de site / jardin remarquable / musée en zone rurale" : "musée en milieu rural",
            "maison musée / maison des illustres / musée en zone rurale" : "musée en milieu rural",
            "musée littéraire / maison des illustres / musée en zone rurale": "musée en milieu rural",
            "maison d'artiste / musée littéraire / maison des illustres": "maison musée",
            "maison musée / maison des illustres / jardin remarquable" : "maison musée",
            "maison musée / / maison des illustres / musée en milieu rural" : "musée en milieu rural",
            "musée de mode/ maison des illustres" : "musée de mode",
            "musée de site / maison d'artiste / musée d'art sacré" : "maison musée",
            "jardin remarquable / musée en milieu rural" : "musée en milieu rural",
            "maison musée / musée littéraire / maison des illustres / jardin remarquable" : "maison musée littéraire",
            "musée de site / maison musée / musée littéraire / maison des illustres" : "maison musée littéraire",
            "maison musée / musée littéraire" : "maison musée littéraire",
            "musée littéraire / maison des illustres / musée en milieu rural" : "musée en milieu rural",
            "maison musée / musée littéraire / maison des illustres / musée en milieu rural" : "musée en milieu rural",
            "maison musée / musée littéraire / maison des illustres" : "maison musée littéraire",
            "musée littéraire / maison des illustres" : "maison musée littéraire"
        }

        # 3. Application du mapping
        # Si une catégorie n'est pas dans le dictionnaire, on garde le texte nettoyé original
        df["categorie"] = df["categorie"].replace(map_cat)
        
        # Petit regroupement pour les cas très rares (< 10 musées)
        # On les met dans "Autre" pour éviter d'avoir des colonnes inutiles
        top_cats = df["categorie"].value_counts()
        rares = top_cats[top_cats < 10].index
        df.loc[df["categorie"].isin(rares), "categorie"] = "Autre"

        return df