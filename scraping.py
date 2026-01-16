# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------------
PROJET      : Analyse du Marché de l'Emploi (SAé Data)
FICHIER     : scraping.py
DESCRIPTION : Script d'extraction automatisée des offres d'emploi sur HelloWork.
DATE        : Janvier 2026
--------------------------------------------------------------------------------
"""

import time
import pandas as pd
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# --- CONFIGURATION DU SCRAPING ---
OBJECTIF = 1000  # Nombre d'offres à récupérer
VILLE = ""  # Laisser vide pour une recherche "France Entière"
NOM_FICHIER = "dataset_hellowork_v3_france.csv"


def lancer_scraping_france():
    """
    Fonction principale du robot d'extraction.
    Parcourt les pages de résultats, extrait les données brutes et sauvegarde en CSV.
    """
    print(f"--- 🇫🇷 Démarrage du scraping FRANCE ENTIÈRE : Objectif {OBJECTIF} offres ---")

    # 1. Configuration du navigateur (Chrome)
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Mode sans interface graphique (activé en prod)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # User-Agent : Indispensable pour ne pas être détecté comme un robot basique
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 2. Initialisation du Driver Selenium
    # Gestion automatique de la version du ChromeDriver
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print("⚠️ Erreur lancement driver standard, tentative avec Service...")
        driver = webdriver.Chrome(service=Service(), options=options)

    # Construction de l'URL de recherche
    url_base = f"https://www.hellowork.com/fr-fr/emploi/recherche.html?k={VILLE}"
    driver.get(url_base)

    donnees = []
    page = 1

    try:
        # Pause pour laisser le temps au JavaScript de charger
        time.sleep(2)

        # Gestion de la bannière Cookies (si elle apparaît)
        try:
            driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
        except:
            pass  # On ignore si le bouton n'est pas là

        # --- BOUCLE PRINCIPALE ---
        while len(donnees) < OBJECTIF:
            print(f"📄 Page {page} | Stock : {len(donnees)} offres collectées")

            # Récupération de toutes les "cartes" offres de la page courante
            cartes = driver.find_elements(By.CSS_SELECTOR, "[data-cy='serpCard']")

            if not cartes:
                print("⚠️ Plus d'offres trouvées ou blocage de sécurité.")
                break

            for carte in cartes:
                try:
                    # A. Extraction Titre & Entreprise
                    # On utilise une logique robuste : parfois c'est h3, parfois des p
                    h3 = carte.find_element(By.TAG_NAME, "h3")
                    ps = h3.find_elements(By.TAG_NAME, "p")

                    if len(ps) >= 2:
                        titre = ps[0].get_attribute("textContent").strip()
                        entreprise = ps[1].get_attribute("textContent").strip()
                    else:
                        # Fallback (Plan B) si la structure HTML change
                        full_text = h3.get_attribute("textContent").strip()
                        parts = full_text.split('\n')
                        titre = parts[0].strip()
                        entreprise = parts[1].strip() if len(parts) > 1 else "Inconnu"

                    if not titre: continue

                    # B. Extraction Localisation
                    try:
                        loc = carte.find_element(By.CSS_SELECTOR, "[data-cy='localisationCard']").get_attribute(
                            "textContent").strip()
                    except:
                        loc = "France"

                    # C. Extraction Contrat
                    try:
                        contrat = carte.find_element(By.CSS_SELECTOR, "[data-cy='contractCard']").get_attribute(
                            "textContent").strip()
                    except:
                        contrat = "Non spécifié"

                    # D. Extraction Salaire (Parsing du texte global)
                    salaire = "Non affiché"
                    carte_text = carte.get_attribute("textContent")
                    if "€" in carte_text:
                        import re
                        # Regex pour trouver une séquence de chiffres suivie du symbole €
                        match = re.search(r'([0-9\s]+€.*)', carte_text)
                        if match:
                            salaire = match.group(1).strip()
                        else:
                            # Méthode ligne par ligne si la regex échoue
                            for line in carte_text.split('\n'):
                                if "€" in line:
                                    salaire = line.strip()
                                    break

                    # E. Extraction Lien
                    try:
                        lien = carte.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except:
                        lien = "Non disponible"

                    # Ajout au dataset
                    donnees.append({
                        "Titre": titre,
                        "Entreprise": entreprise,
                        "Localisation": loc,
                        "Contrat": contrat,
                        "Salaire": salaire,
                        "Lien": lien
                    })

                    # Arrêt immédiat si l'objectif est atteint
                    if len(donnees) >= OBJECTIF: break

                except Exception as e:
                    continue  # Si une carte bugue, on passe à la suivante

            # Passage à la page suivante
            page += 1
            driver.get(f"{url_base}&p={page}")

            # PAUSE ALÉATOIRE : Crucial pour éviter le blocage IP (Anti-bot)
            time.sleep(random.uniform(1.0, 2.2))

    finally:
        # Fermeture propre du navigateur dans tous les cas
        try:
            driver.quit()
        except:
            pass

    # 3. Exportation des données
    if donnees:
        df = pd.DataFrame(donnees)
        # Encodage utf-8-sig pour compatibilité Excel parfaite
        df.to_csv(NOM_FICHIER, index=False, encoding='utf-8-sig', sep=';')
        print(f"\n✨ SUCCÈS ! Fichier '{NOM_FICHIER}' généré avec {len(df)} lignes.")
    else:
        print("❌ ÉCHEC : Aucune donnée récupérée.")


if __name__ == "__main__":
    lancer_scraping_france()