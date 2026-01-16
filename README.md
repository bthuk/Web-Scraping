

#  Analyse du Marché de l'Emploi - HelloWork (2026)

Ce projet de Data Analysis vise à **récupérer, nettoyer et visualiser** les données réelles du marché de l'emploi en France. À partir d'offres brutes extraites de *HelloWork*, nous avons créé un tableau de bord décisionnel permettant d'analyser les salaires, les types de contrats et la répartition géographique des offres.




## Installation

1. **Cloner le projet** ou télécharger les fichiers.
2. **Installer les dépendances Python** :
```bash
pip install pandas selenium

```


*(Note : Selenium gère désormais automatiquement les drivers Chrome).*

##  Utilisation (Pipeline)

Le projet fonctionne en 3 étapes séquentielles :

### 1. Collecte des données (Scraping)

Lancez le robot pour récupérer les dernières offres en ligne.

```bash
python scraping.py

```

> *Output : Crée le fichier `dataset_hellowork_v3_france.csv` (Données brutes).*

### 2. Nettoyage et Traitement (ETL)

Lancez le script de nettoyage pour normaliser les salaires (conversion en Annuel Brut), nettoyer les titres et séparer Ville/Département.

```bash
python traitement.py

```

> *Output : Crée le fichier `dataset_clean_final.csv` (Données propres).*

### 3. Visualisation

Ouvrez le fichier **`scrap.pbix`** avec **Microsoft Power BI Desktop**.
Cliquez sur le bouton **"Actualiser"** pour charger les nouvelles données du fichier CSV propre.

##  Structure du Projet

```text
 Projet-HelloWork
│
├── 📜 scraping.py              # Script d'extraction (Selenium)
├── 📜 traitement.py            # Script de nettoyage (Pandas/Regex)
├── 📊 dataset_clean_final.csv  # Le jeu de données final prêt pour l'analyse
├── 📈 scrap.pbix               # Le Dashboard Power BI
└── 📝 README.md                # Documentation

```



*Projet universitaire réalisé en Janvier 2026.*
