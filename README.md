# Projet Python pour la Data Science : Analyse et Prédiction de la Fréquentation des Musées

**Auteurs :** Emma Bezombes, Clara Mihailescu, Valentine Labbé

## Sujet

Le secteur culturel, et plus particulièrement les musées, fait face à des enjeux de gestion majeurs : volatilité des publics, contraintes budgétaires et nécessité d'adapter l'offre culturelle aux territoires.

La fréquentation d'un musée n'est pas seulement un chiffre comptable ; c'est le reflet de l'attractivité d'un territoire et de la pertinence d'une collection. Si des institutions comme le Louvre semblent hors normes, la grande majorité des 1 200 musées français obéit à des dynamiques que l'on peut tenter de modéliser.

L'objectif de ce projet est de construire des outils d'analyse capables non seulement de prévoir les flux de visiteurs, mais aussi de comprendre les facteurs déterminants du succès. Nous avons ainsi cherché à opposer une vision comptable (prévision budgétaire) à une vision structurelle (analyse de l'offre et du territoire).

## Problématique

**Dans quelle mesure est-il possible de prédire la fréquentation annuelle d'un musée en France ?**

Plus spécifiquement : peut-on dissocier la part de fréquentation due à l'inertie historique (habitudes, renommée) de la part due aux caractéristiques physiques intrinsèques (thème, géographie, surface) ?

## Architecture du projet

Le code est réparti en 5 notebooks pour faciliter la lecture et la maintenance. Il est recommandé de les consulter dans l'ordre suivant :

1.  `00_plan_et_intro.ipynb` : Introduction, définitions et plan détaillé.
2.  `01_construction_base.ipynb` : Nettoyage des données (Data Cleaning) et Feature Engineering.
3.  `02_stat_desc.ipynb` : Statistiques descriptives et visualisations.
4.  `03_modelisation.ipynb` : Entraînement des modèles (Lasso et Random Forest).
5.  `04_conclusion.ipynb` : Analyse des résultats et bilan.

## Modèles utilisés

Nous avons mis en œuvre une approche comparative basée sur deux types de régressions supervisées :

1.  **Modèle LASSO (Approche de Gestion) :**
    * *Objectif :* Prédiction budgétaire à court terme (N+1).
    * *Spécificité :* Utilise l'historique de fréquentation (N-1) et les ratios de gestion.
    * *Performance :* R² env. 0.82. Excellente précision grâce à la forte inertie des comportements.

2.  **Modèle Random Forest (Approche Structurelle) :**
    * *Objectif :* Analyse de l'importance des facteurs (Feature Importance).
    * *Spécificité :* Il ne connaît pas le passé. Il prédit uniquement en fonction de la géographie (GPS, région) et de l'offre (Thème, Label).
    * *Performance :* R² env. 0.45. Ce score plus faible permet d'isoler la part de fréquentation qui ne dépend que de l'infrastructure ("Potentiel théorique").

### 3. Données et Sources
Pour réaliser ce projet, nous avons agrégé trois bases de données distinctes issues de l'Open Data du Ministère de la Culture :

1.  **Fréquentation des musées de France :** Les volumes globaux de visiteurs par établissement.
2.  **Entrées et catégories du public :** Le détail des types de visiteurs (payants, gratuits, scolaires, groupes).
3.  **Muséofile :** Le répertoire administratif fournissant les données structurelles (coordonnées GPS, surface, année de création, label).

Le croisement de ces sources nous a permis de constituer un jeu de données unique, nettoyé et enrichi, couvrant la période d'analyse.

## Installation et Reproduction

Pour reproduire l'environnement de développement, veuillez installer les dépendances nécessaires :
```bash
pip install -r requirements.txt

