# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------------
PROJET      : Analyse du Marché de l'Emploi (SAé Data)
FICHIER     : traitement.py
DESCRIPTION : Pipeline de nettoyage et de standardisation des données (ETL).
              Transforme les données brutes (Scraping) en données exploitables (BI).
DATE        : Janvier 2026
--------------------------------------------------------------------------------
"""

import pandas as pd
import re
import os

# --- CONFIGURATION ---
DOSSIER = r"C:\Users\uberthon\Downloads\scap"
FICHIER_ENTREE = os.path.join(DOSSIER, "dataset_hellowork_v3_france.csv")
FICHIER_SORTIE = os.path.join(DOSSIER, "dataset_clean_final.csv")


def nettoyer_salaire(texte_salaire):
    """
    Convertit une chaîne de caractères hétérogène en un flottant (Salaire Annuel Brut).

    Args:
        texte_salaire (str): Ex: "2000 € / mois", "35k €", "12 € / heure"

    Returns:
        float: Le salaire ramené à l'année (ex: 24000.0) ou None si invalide.
    """
    # 1. Gestion des valeurs nulles ou masquées
    if not isinstance(texte_salaire, str) or "non affiché" in texte_salaire.lower():
        return None

    # 2. Nettoyage préliminaire (suppression espaces, symboles invisibles, conversion k->000)
    clean_txt = texte_salaire.lower().replace(" ", "").replace("\u202f", "").replace("\xa0", "").replace("k", "000")

    # 3. Extraction des valeurs numériques via Regex
    nombres = re.findall(r'(\d+(?:\.\d+)?)', clean_txt)
    if not nombres: return None

    # Si une fourchette est donnée (ex: 30000-40000), on prend la moyenne
    valeur = sum([float(n) for n in nombres]) / len(nombres)

    # 4. Logique de standardisation temporelle (Tout -> Annuel)
    multiplicateur = 1.0

    if "mois" in clean_txt:
        multiplicateur = 12.0
    elif "heure" in clean_txt:
        multiplicateur = 151.67 * 12  # Base 35h (151.67h/mois) sur 12 mois
    elif "jour" in clean_txt:
        multiplicateur = 218.0  # Convention forfait jour cadre moyen
    elif 1200 <= valeur <= 12000:
        # Heuristique : Si aucune unité n'est précisée mais que le chiffre est
        # entre 1200 et 12000, il s'agit statistiquement d'un salaire mensuel.
        multiplicateur = 12.0

    salaire_annuel = valeur * multiplicateur

    # 5. Filtrage des valeurs aberrantes (Erreurs de saisie)
    # On exclut les salaires impossibles (< 14k ou > 200k pour ce scope)
    if salaire_annuel < 14000 or salaire_annuel > 200000:
        return None

    return round(salaire_annuel, 2)


def simplifier_titre(titre_brut):
    """
    Nettoie le titre de l'offre pour le rendre lisible dans les graphiques.
    Supprime le 'bruit' (H/F, contrat, horaires).
    """
    if not isinstance(titre_brut, str): return "Inconnu"

    titre_clean = titre_brut

    # Suppression des mentions horaires (ex: 35h, 39H)
    titre_clean = re.sub(r'\d+(?:[\.,]\d+)?\s?[hH]', "", titre_clean)

    # Liste des mots-clés parasites à supprimer
    mots_a_supprimer = [
        r"temps\s?plein", r"temps\s?partiel",
        r"\bCDI\b", r"\bCDD\b", r"\bIntérim\b", r"\bStage\b", r"\bAlternance\b",
        r"\bH/F\b", r"\bF/H\b", r"\(.*?\)",  # Tout ce qui est entre parenthèses
        r"\s-\s", r"\|"  # Tirets et barres isolés
    ]

    for motif in mots_a_supprimer:
        titre_clean = re.sub(motif, " ", titre_clean, flags=re.IGNORECASE)

    # Suppression des espaces multiples et mise en forme
    return re.sub(r"\s+", " ", re.sub(r"[-_]", " ", titre_clean)).strip().capitalize()


def separer_localisation(loc_brute):
    """
    Sépare la chaîne de localisation brute en (Ville, Département).
    Exemple : 'Paris 15e - 75' -> Ville='Paris', Dept='75'
    """
    if not isinstance(loc_brute, str):
        return pd.Series(["Inconnu", "Inconnu"])

    # Séparation sur le dernier tiret trouvé
    parts = loc_brute.rsplit(' - ', 1)

    if len(parts) == 2:
        ville = parts[0].strip()
        dept = parts[1].strip()
    else:
        ville = loc_brute.strip()
        dept = "France"

    # Nettoyage spécifique des arrondissements pour regrouper les grandes villes
    # Ex: "Paris 15e" devient "Paris"
    ville = re.sub(r'\s\d+(?:er|e|ème)?$', '', ville)

    return pd.Series([ville, dept])


def lancer_traitement_final():
    """
    Orchestrateur du nettoyage.
    Charge le CSV, applique les fonctions, dédoublonne et exporte.
    """
    print(f"--- 🧹 Démarrage du Pipeline de Traitement des Données ---")

    if not os.path.exists(FICHIER_ENTREE):
        print(f"❌ ERREUR CRITIQUE : Le fichier {FICHIER_ENTREE} est introuvable.")
        return

    # 1. Chargement (Gestion robuste des séparateurs CSV)
    try:
        df = pd.read_csv(FICHIER_ENTREE, sep=';', on_bad_lines='skip', engine='python')
    except:
        df = pd.read_csv(FICHIER_ENTREE, sep=',', on_bad_lines='skip', engine='python')
    print(f"✅ Chargement réussi : {len(df)} lignes brutes importées.")

    # 2. Application des transformations
    print("... Normalisation des salaires (Mensuel/Horaire -> Annuel)")
    df['Salaire_Annuel'] = df['Salaire'].apply(nettoyer_salaire)

    print("... Nettoyage sémantique des titres")
    df['Titre_Simplifie'] = df['Titre'].apply(simplifier_titre)

    print("... Structuration géographique (Ville / Département)")
    df[['Ville', 'Departement']] = df['Localisation'].apply(separer_localisation)

    # 3. Sélection des features (colonnes) pertinentes pour Power BI
    cols = ['Titre_Simplifie', 'Entreprise', 'Ville', 'Departement', 'Contrat', 'Salaire_Annuel']

    # Vérification de l'existence des colonnes
    cols_existantes = [c for c in cols if c in df.columns]
    df_clean = df[cols_existantes].copy()

    # 4. Dédoublonnage
    # On supprime les offres identiques (même titre, même boite, même ville)
    df_clean.drop_duplicates(subset=['Titre_Simplifie', 'Entreprise', 'Ville'], inplace=True)

    # 5. Exportation
    df_clean.to_csv(FICHIER_SORTIE, index=False, encoding='utf-8-sig', sep=',')

    print("\n--- 🎉 TRAITEMENT TERMINÉ ---")
    print(f"Fichier final généré : {FICHIER_SORTIE}")
    print(f"Statistiques :")
    print(f" - Offres uniques : {len(df_clean)}")
    print(f" - Salaires exploitables : {df_clean['Salaire_Annuel'].notna().sum()}")


if __name__ == "__main__":
    lancer_traitement_final()