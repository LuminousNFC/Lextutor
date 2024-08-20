# -*- coding: utf-8 -*-
import os
import json
import logging
import sys
import re
import time
from functools import lru_cache
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Dict, Any

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration des liens Fedlex
FEDLEX_LINKS = {
    "CC": {"lien": "https://www.fedlex.admin.ch/eli/cc/24/233_245_233/fr", "titre": "Code civil"},
    "CO": {"lien": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr", "titre": "Code des obligations"},
    "CP": {"lien": "https://www.fedlex.admin.ch/eli/cc/54/757_781_799/fr", "titre": "Code pénal"},
    "CPM": {"lien": "https://www.fedlex.admin.ch/eli/cc/43/359_375_369/fr", "titre": "Code pénal militaire"},
    "CPC": {"lien": "https://www.fedlex.admin.ch/eli/cc/2010/262/fr", "titre": "Code de procédure civile"},
    "CPP": {"lien": "https://www.fedlex.admin.ch/eli/cc/2010/267/fr", "titre": "Code de procédure pénale"},
    "Cst": {"lien": "https://www.fedlex.admin.ch/eli/cc/1999/404/fr", "titre": "Constitution fédérale"},
    "LAA": {"lien": "https://www.fedlex.admin.ch/eli/cc/1982/1676_1676_1676/fr", "titre": "Loi fédérale sur l'assurance-accidents"},
    "LACI": {"lien": "https://www.fedlex.admin.ch/eli/cc/1982/2184_2184_2184/fr", "titre": "Loi sur l'assurance-chômage"},
    "LAgr": {"lien": "https://www.fedlex.admin.ch/eli/cc/1998/3033_3033_3033/fr", "titre": "Loi sur l'agriculture"},
    "LAI": {"lien": "https://www.fedlex.admin.ch/eli/cc/1959/827_857_845/fr", "titre": "Loi fédérale sur l'assurance-invalidité"},
    "LAMal": {"lien": "https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/fr", "titre": "Loi fédérale sur l'assurance-maladie"},
    "LAS": {"lien": "https://www.fedlex.admin.ch/eli/cc/1978/1456_1456_1456/fr", "titre": "Loi fédérale en matière d'assistance"},
    "LAT": {"lien": "https://www.fedlex.admin.ch/eli/cc/1979/1573_1573_1573/fr", "titre": "Loi sur l'aménagement du territoire"},
    "LAVS": {"lien": "https://www.fedlex.admin.ch/eli/cc/1952/1021_1046_1050/fr", "titre": "Loi fédérale sur l'assurance-vieillesse et survivants"},
    "LB": {"lien": "https://www.fedlex.admin.ch/eli/cc/51/117_121_129/fr", "titre": "Loi sur les banques"},
    "LBA": {"lien": "https://www.fedlex.admin.ch/eli/cc/1998/892_892_892/fr", "titre": "Loi sur le blanchiment d'argent"},
    "LBFA": {"lien": "https://www.fedlex.admin.ch/eli/cc/1979/570_570_570/fr", "titre": "Loi fédérale sur le bail à ferme agricole"},
    "LBI": {"lien": "https://www.fedlex.admin.ch/eli/cc/1955/871_893_899/fr", "titre": "Loi sur les brevets"},
    "LBVM": {"lien": "https://www.fedlex.admin.ch/eli/cc/1997/68_68_68/fr", "titre": "Loi sur les bourses"},
    "LCA": {"lien": "https://www.fedlex.admin.ch/eli/cc/24/719_735_717/fr", "titre": "Loi fédérale sur le contrat d'assurance"},
    "LCaim": {"lien": "https://www.fedlex.admin.ch/eli/cc/2020/982/fr", "titre": "Loi sur les cautionnements solidaires liés au COVID-19"},
    "LCAP": {"lien": "https://www.fedlex.admin.ch/eli/cc/1994/2806_2806_2806/fr", "titre": "Loi encourageant la construction et l'accession à la propriété de logements"},
    "LCART": {"lien": "https://www.fedlex.admin.ch/eli/cc/1996/546_546_546/fr", "titre": "Loi sur les cartels"},
    "LCdF": {"lien": "https://www.fedlex.admin.ch/eli/cc/1958/335_341_347/fr", "titre": "Loi sur les chemins de fer"},
    "LChim": {"lien": "https://www.fedlex.admin.ch/eli/cc/2004/724/fr", "titre": "Loi sur les produits chimiques"},
    "LChP": {"lien": "https://www.fedlex.admin.ch/eli/cc/1988/506_506_506/fr", "titre": "Loi sur la chasse"},
    "LCITES": {"lien": "https://www.fedlex.admin.ch/eli/cc/2013/600/fr", "titre": "Loi fédérale sur la circulation des espèces de faune et de flore protégées"},
    "LCR": {"lien": "https://www.fedlex.admin.ch/eli/cc/1959/679_705_685/fr", "titre": "Loi sur la circulation routière"},
    "LDA": {"lien": "https://www.fedlex.admin.ch/eli/cc/1993/1798_1798_1798/fr", "titre": "Loi sur le droit d'auteur"},
    "LDIP": {"lien": "https://www.fedlex.admin.ch/eli/cc/1988/1776_1776_1776/fr", "titre": "Loi fédérale sur le droit international privé"},
    "LEaux": {"lien": "https://www.fedlex.admin.ch/eli/cc/2018/801/fr", "titre": "Loi fédérale sur la protection des eaux"},
    "LEFin": {"lien": "https://www.fedlex.admin.ch/eli/cc/2018/801/fr", "titre": "Loi sur les établissements financiers"},
    "LEg": {"lien": "https://www.fedlex.admin.ch/eli/cc/1996/1498_1498_1498/fr", "titre": "Loi sur l'égalité"},
    "LEHE": {"lien": "https://www.fedlex.admin.ch/eli/cc/2014/691/fr", "titre": "Loi sur l'encouragement et la coordination des hautes écoles"},
    "LEI": {"lien": "https://www.fedlex.admin.ch/eli/cc/2007/758/fr", "titre": "Loi fédérale sur les étrangers et l'intégration"},
    "LEmb": {"lien": "https://www.fedlex.admin.ch/eli/cc/2002/564/fr", "titre": "Loi sur les embargos"},
    "LEne": {"lien": "https://www.fedlex.admin.ch/eli/fga/2023/1603/fr", "titre": "Loi sur l'énergie"},
    "LEnu": {"lien": "https://www.fedlex.admin.ch/eli/cc/2004/723/fr", "titre": "Loi sur les énergies renouvelables"},
    "LFo": {"lien": "https://www.fedlex.admin.ch/eli/cc/1992/2521_2521_2521/fr", "titre": "Loi sur les forêts"},
    "LFH": {"lien": "https://www.fedlex.admin.ch/eli/cc/33/189_191_191/fr", "titre": "Loi sur les forces hydrauliques"},
    "LFAIE": {"lien": "https://www.fedlex.admin.ch/eli/cc/1984/1148_1148_1148/fr", "titre": "Loi fédérale sur l'acquisition d'immeubles par des personnes à l'étranger"},
    "LFINMA": {"lien": "https://www.fedlex.admin.ch/eli/cc/2008/736/fr", "titre": "Loi sur l'Autorité fédérale de surveillance des marchés financiers"},
    "LFLP": {"lien": "https://www.fedlex.admin.ch/eli/fga/2024/913/fr", "titre": "Loi sur le libre passage"},
    "LFPr": {"lien": "https://www.fedlex.admin.ch/eli/cc/2002/728/fr", "titre": "Loi sur la formation professionnelle"},
    "LFSP": {"lien": "https://www.fedlex.admin.ch/eli/cc/1991/2259_2259_2259/fr", "titre": "Loi fédérale sur la pêche"},
    "LFus": {"lien": "https://www.fedlex.admin.ch/eli/cc/2004/320/fr", "titre": "Loi sur la fusion"},
    "LGA": {"lien": "https://www.fedlex.admin.ch/eli/cc/1995/2513/fr", "titre": "Loi sur le génie génétique"},
    "LGéo": {"lien": "https://www.fedlex.admin.ch/eli/cc/2008/388/fr", "titre": "Loi sur la géoinformation"},
    "LGG": {"lien": "https://www.fedlex.admin.ch/eli/cc/2003/705/fr", "titre": "Loi sur le génie génétique"},
    "LHand": {"lien": "https://www.fedlex.admin.ch/eli/cc/2003/667/fr", "titre": "Loi sur l'égalité pour les handicapés"},
    "LIFD": {"lien": "https://www.fedlex.admin.ch/eli/cc/1991/1184_1184_1184/fr", "titre": "Loi fédérale sur l'impôt fédéral direct"},
    "LHID": {"lien": "https://www.fedlex.admin.ch/eli/cc/1991/1256_1256_1256/fr", "titre": "Loi fédérale sur l'harmonisation des impôts directs des cantons et des communes"},
    "LMCFA": {"lien": "https://www.fedlex.admin.ch/eli/cc/2006/440/fr", "titre": "Loi sur le Contrôle fédéral des finances"},
    "LMP": {"lien": "https://www.fedlex.admin.ch/eli/cc/2020/126/fr", "titre": "Loi fédérale sur les marchés publics"},
    "LMSI": {"lien": "https://www.fedlex.admin.ch/eli/cc/1998/1546_1546_1546/fr", "titre": "Loi fédérale instituant des mesures visant au maintien de la sûreté intérieure"},
    "LN": {"lien": "https://www.fedlex.admin.ch/eli/cc/2016/404/fr", "titre": "Loi sur la nationalité suisse"},
    "LPA": {"lien": "https://www.fedlex.admin.ch/eli/cc/1969/737_757_755/fr", "titre": "Loi fédérale sur la procédure administrative"},
    "LPAC": {"lien": "https://www.fedlex.admin.ch/eli/cc/2015/435/fr", "titre": "Loi sur la poste"},
    "LPC": {"lien": "https://www.fedlex.admin.ch/eli/cc/2007/804/fr", "titre": "Loi sur les prestations complémentaires à l'AVS et à l’AI"},
    "LPCC": {"lien": "https://www.fedlex.admin.ch/eli/cc/2006/822/fr", "titre": "Loi fédérale sur les fonds de placement"},
    "LPCy": {"lien": "https://www.fedlex.admin.ch/eli/cc/2022/614/fr", "titre": "Loi fédérale sur la cybersécurité"},
    "LPE": {"lien": "https://www.fedlex.admin.ch/eli/cc/1984/1122_1122_1122/fr", "titre": "Loi sur la protection de l'environnement"},
    "LPers": {"lien": "https://www.fedlex.admin.ch/eli/cc/2001/123/fr", "titre": "Loi sur le personnel de la Confédération"},
    "LPGA": {"lien": "https://www.fedlex.admin.ch/eli/cc/2002/510/fr", "titre": "Loi fédérale sur la partie générale du droit des assurances sociales"},
    "LPD": {"lien": "https://www.fedlex.admin.ch/eli/cc/2022/491/fr", "titre": "Loi fédérale sur la protection des données"},
    "LPM": {"lien": "https://www.fedlex.admin.ch/eli/cc/1993/274_274_274/fr", "titre": "Loi sur la protection des marques"},
    "LPMA": {"lien": "https://www.fedlex.admin.ch/eli/cc/2001/118/fr", "titre": "Loi fédérale sur la procréation médicalement assistée"},
    "LPN": {"lien": "https://www.fedlex.admin.ch/eli/cc/1966/1637_1694_1679/fr", "titre": "Loi fédérale sur la protection de la nature et du paysage"},
    "LPP": {"lien": "https://www.fedlex.admin.ch/eli/cc/1983/797_797_797/fr", "titre": "Loi fédérale sur la prévoyance professionnelle vieillesse, survivants et invalidité"},
    "LRTV": {"lien": "https://www.fedlex.admin.ch/eli/cc/2007/150/fr", "titre": "Loi sur la radio et la télévision"},
    "LRENS": {"lien": "https://www.fedlex.admin.ch/eli/cc/2017/494/fr", "titre": "Loi sur le renseignement"},
    "LRHa": {"lien": "https://www.fedlex.admin.ch/eli/cc/2016/365/fr", "titre": "Loi fédérale sur l'harmonisation des registres des habitants et d'autres registres officiels de personnes"},
    "LRH": {"lien": "https://www.fedlex.admin.ch/eli/cc/2013/617/fr", "titre": "Loi relative à la recherche sur l'être humain"},
    "LRV": {"lien": "https://www.fedlex.admin.ch/eli/cc/2005/707/fr", "titre": "Loi sur les recueils du droit fédéral et la Feuille fédérale"},
    "LSA": {"lien": "https://www.fedlex.admin.ch/eli/cc/2005/735/fr", "titre": "Loi sur la surveillance des assurances"},
    "LSFin": {"lien": "https://www.fedlex.admin.ch/eli/cc/2018/801/fr", "titre": "Loi sur les établissements financiers"},
    "LStup": {"lien": "https://www.fedlex.admin.ch/eli/cc/1952/241_241_245/fr", "titre": "Loi fédérale sur les stupéfiants et les substances psychotropes"},
    "LTAF": {"lien": "https://www.fedlex.admin.ch/eli/cc/2006/352/fr", "titre": "Loi sur le Tribunal administratif fédéral"},
    "LTC": {"lien": "https://www.fedlex.admin.ch/eli/cc/1997/2187_2187_2187/fr", "titre": "Loi sur les télécommunications"},
    "LTV": {"lien": "https://www.fedlex.admin.ch/eli/cc/2009/680/fr", "titre": "Loi sur le transport de voyageurs"},
    "LTVA": {"lien": "https://www.fedlex.admin.ch/eli/cc/2009/615/fr", "titre": "Loi sur la TVA"},
    "LTr": {"lien": "https://www.fedlex.admin.ch/eli/cc/1966/57_57_57/fr", "titre": "Loi sur le travail"},
    "LUMV": {"lien": "https://www.fedlex.admin.ch/eli/cc/1993/478_478_478/fr", "titre": "Loi sur l'unité monétaire et les moyens de paiement"},
    "LVC": {"lien": "https://www.fedlex.admin.ch/eli/cc/2022/790/fr", "titre": "Loi fédérale les voies cyclables"}
}

# Définir les paramètres d'extraction de Fedlex
FEDLEX_EXTRACTION_SETTINGS = {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 5,
    "rate_limit_delay": 1  # Délai entre les requêtes en secondes
}

last_request_time = 0

def setup_driver() -> webdriver.Chrome:
    """
    Configure et retourne une instance de Chrome WebDriver.

    Returns:
        webdriver.Chrome: Instance de Chrome WebDriver.
    """
    chromedriver_autoinstaller.install()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException as e:
        logger.error(f"Erreur lors de la création du webdriver: {e}")
        raise

def extract_content(element, level=0) -> str:
    """
    Extrait et formate le contenu HTML d'un élément BeautifulSoup.

    Args:
        element (bs4.element.Tag): Élément BeautifulSoup à extraire.
        level (int): Niveau d'indentation pour le formatage.

    Returns:
        str: Contenu HTML formaté.
    """
    content = ""
    for child in element.children:
        if child.name in ['p', 'div']:
            content += f"{'  ' * level}<p>{child.get_text().strip()}</p>\n"
        elif child.name in ['ul', 'ol']:
            content += f"{'  ' * level}<{child.name}>\n"
            for li in child.find_all('li', recursive=False):
                content += f"{'  ' * (level+1)}<li>{li.get_text().strip()}</li>\n"
                content += extract_content(li, level+2)
            content += f"{'  ' * level}</{child.name}>\n"
    return content

def normalize_law_code(law_code: str) -> str:
    """
    Normalise le code de la loi.

    Args:
        law_code (str): Code de la loi.

    Returns:
        str: Code de la loi normalisé.
    """
    law_code = law_code.strip().upper()
    if law_code in ["CST", "CST."]:
        return "Cst"
    return law_code

def rate_limit():
    """
    Implémente un rate limiting basique.
    """
    global last_request_time
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    if time_since_last_request < FEDLEX_EXTRACTION_SETTINGS['rate_limit_delay']:
        time.sleep(FEDLEX_EXTRACTION_SETTINGS['rate_limit_delay'] - time_since_last_request)
    last_request_time = time.time()

@lru_cache(maxsize=100)
def extract_fedlex_article(law_abbreviation: str, article_number: str) -> Dict[str, Any]:
    """
    Extrait le contenu d'un article de loi depuis Fedlex.

    Args:
        law_abbreviation (str): Abréviation de la loi.
        article_number (str): Numéro de l'article.

    Returns:
        Dict[str, Any]: Dictionnaire contenant les informations de l'article.

    Raises:
        ValueError: Si la loi n'est pas reconnue.
    """
    for attempt in range(FEDLEX_EXTRACTION_SETTINGS['max_retries']):
        try:
            rate_limit()
            law_abbreviation = normalize_law_code(law_abbreviation)
            
            logger.info(f"Code de loi reçu: {law_abbreviation}")
            logger.info(f"Code de loi normalisé: {law_abbreviation}")

            if law_abbreviation not in FEDLEX_LINKS:
                raise ValueError(f"Loi non reconnue: {law_abbreviation}")

            base_url = FEDLEX_LINKS[law_abbreviation]["lien"]
            article_id = re.sub(r'(\d+)([a-z])', r'\1_\2', article_number.lower())
            article_url = f"{base_url}#art_{article_id}"
            
            logger.info(f"Tentative {attempt + 1} - URL de l'article : {article_url}")

            driver = setup_driver()
            try:
                driver.get(article_url)
                WebDriverWait(driver, FEDLEX_EXTRACTION_SETTINGS['timeout']).until(
                    EC.presence_of_element_located((By.ID, f"art_{article_id}"))
                )
                
                time.sleep(2)
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                article_content = soup.find('article', id=f"art_{article_id}")
                if not article_content:
                    raise ValueError("Contenu de l'article non trouvé.")

                title = article_content.find('h5', class_='article-title')
                title_text = title.get_text().strip() if title else f"Article {article_number}"
                
                formatted_content = f"<h2>{FEDLEX_LINKS[law_abbreviation]['titre']} - {title_text}</h2>\n"
                formatted_content += extract_content(article_content)

                return {
                    "success": True,
                    "law_code": law_abbreviation,
                    "article_number": article_number,
                    "title": title_text,
                    "content": formatted_content
                }
            finally:
                driver.quit()
        except (UnicodeDecodeError, TimeoutException, NoSuchElementException) as e:
            logger.error(f"Erreur lors de l'extraction de l'article {law_abbreviation} {article_number} (tentative {attempt + 1}): {e}")
            if attempt < FEDLEX_EXTRACTION_SETTINGS['max_retries'] - 1:
                logger.info(f"Nouvelle tentative dans {FEDLEX_EXTRACTION_SETTINGS['retry_delay']} secondes...")
                time.sleep(FEDLEX_EXTRACTION_SETTINGS['retry_delay'])
            else:
                return {
                    "success": False,
                    "law_code": law_abbreviation,
                    "article_number": article_number,
                    "title": "",
                    "content": "",
                    "error": str(e)
                }

    return {
        "success": False,
        "law_code": law_abbreviation,
        "article_number": article_number,
        "title": "",
        "content": "",
        "error": "Nombre maximal de tentatives atteint"
    }

def validate_input(law_code: str, article_number: str) -> bool:
    """
    Valide les entrées utilisateur.

    Args:
        law_code (str): Code de la loi.
        article_number (str): Numéro de l'article.

    Returns:
        bool: True si les entrées sont valides, False sinon.
    """
    if not re.match(r'^[A-Za-z.]+$', law_code):
        logger.error(f"Code de loi invalide: {law_code}")
        return False
    if not re.match(r'^\d+[a-z]?$', article_number):
        logger.error(f"Numéro d'article invalide: {article_number}")
        return False
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"success": False, "error": "Usage: python fedlex_extractor.py <law_code> <article_number>"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    law_code = sys.argv[1]
    article_number = sys.argv[2]

    if not validate_input(law_code, article_number):
        print(json.dumps({"success": False, "error": "Entrées invalides"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        result = extract_fedlex_article(law_code, article_number)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error(f"Une erreur inattendue s'est produite: {str(e)}")
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)




