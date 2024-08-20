from pydantic import BaseSettings, BaseModel
from typing import Dict, Optional, Any
import requests
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FedlexLink(BaseModel):
    lien: str
    titre: str

class Settings(BaseSettings):
    # Fedlex configuration parameters
    fedlex_links: Dict[str, FedlexLink] = {
    "CC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/24/233_245_233/fr",
        "titre": "Code civil"
    },
    "CO": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/fr",
        "titre": "Code des obligations"
    },
    "CP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/54/757_781_799/fr",
        "titre": "Code pénal"
    },
    "CPC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2010/262/fr",
        "titre": "Code de procédure civile"
    },
    "CPP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2010/267/fr",
        "titre": "Code de procédure pénale"
    },
    "CPM": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/43/359_375_369/fr",
        "titre": "Code pénal militaire"
    },
    "Cst.": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1999/404/fr",
        "titre": "Constitution fédérale"
    },
    "LAA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1982/1676_1676_1676/fr",
        "titre": "Loi fédérale sur l'assurance-accidents"
    },
    "LACI": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1982/2184_2184_2184/fr",
        "titre": "Loi sur l'assurance-chômage"
    },
    "LAgr": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1998/3033_3033_3033/fr",
        "titre": "Loi sur l'agriculture"
    },
    "LAI": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1959/827_857_845/fr",
        "titre": "Loi fédérale sur l'assurance-invalidité"
    },
    "LAMal": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/fr",
        "titre": "Loi fédérale sur l'assurance-maladie"
    },
    "LAS": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1978/1456_1456_1456/fr",
        "titre": "Loi fédérale en matière d'assistance"
    },
    "LAT": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1979/1573_1573_1573/fr",
        "titre": "Loi sur l'aménagement du territoire"
    },
    "LAVS": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1952/1021_1046_1050/fr",
        "titre": "Loi fédérale sur l'assurance-vieillesse et survivants"
    },
    "LB": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/51/117_121_129/fr",
        "titre": "Loi sur les banques"
    },
    "LBA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1998/892_892_892/fr",
        "titre": "Loi sur le blanchiment d'argent"
    },
    "LBFA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1979/570_570_570/fr",
        "titre": "Loi fédérale sur le bail à ferme agricole"
    },
    "LBI": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1955/871_893_899/fr",
        "titre": "Loi sur les brevets"
    },
    "LBVM": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1997/68_68_68/fr",
        "titre": "Loi sur les bourses"
    },
    "LCA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/24/719_735_717/fr",
        "titre": "Loi fédérale sur le contrat d'assurance"
    },
    "LCaim": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2014/769/fr",
        "titre": "Loi sur les cautionnements solidaires liés au COVID-19"
    },
    "LCAP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1994/2806_2806_2806/fr",
        "titre": "Loi encourageant la construction et l'accession à la propriété de logements"
    },
    "LCART": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1996/546_546_546/fr",
        "titre": "Loi sur les cartels"
    },
    "LCdF": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1958/341_341_341/fr",
        "titre": "Loi sur les chemins de fer"
    },
    "LChim": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2009/592/fr",
        "titre": "Loi sur les produits chimiques"
    },
    "LChP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1988/506_506_506/fr",
        "titre": "Loi sur la chasse"
    },
    "LCITES": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2013/600/fr",
        "titre": "Loi fédérale sur la circulation des espèces de faune et de flore protégées"
    },
    "LCR": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1959/679_705_685/fr",
        "titre": "Loi sur la circulation routière"
    },
    "LDIP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1987/1992_1992_1992/fr",
        "titre": "Loi fédérale sur le droit international privé"
    },
    "LEaux": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1992/1860_1860_1860/fr",
        "titre": "Loi fédérale sur la protection des eaux"
    },
    "LEFin": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2018/801/fr",
        "titre": "Loi sur les établissements financiers"
    },
    "LEg": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1996/1498_1498_1498/fr",
        "titre": "Loi sur l'égalité"
    },
    "LEHE": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2014/691/fr",
        "titre": "Loi sur l'encouragement et la coordination des hautes écoles"
    },
    "LEI": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2007/758/fr",
        "titre": "Loi fédérale sur les étrangers et l'intégration"
    },
    "LEmb": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2002/727/fr",
        "titre": "Loi sur les embargos"
    },
    "LEne": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2017/762/fr",
        "titre": "Loi sur l'énergie"
    },
    "LEnu": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2004/723/fr",
        "titre": "Loi sur les énergies renouvelables"
    },
    "LEp": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2015/297/fr",
        "titre": "Loi sur les épidémies"
    },
    "LEpiz": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1966/1621_1621_1621/fr",
        "titre": "Loi sur les épizooties"
    },
    "LFo": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1992/2521_2521_2521/fr",
        "titre": "Loi sur les forêts"
    },
    "LFH": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1917/223_241_241/fr",
        "titre": "Loi sur les forces hydrauliques"
    },
    "LFAIE": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1984/1148_1148_1148/fr",
        "titre": "Loi fédérale sur l'acquisition d'immeubles par des personnes à l'étranger"
    },
    "LFINMA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2008/765/fr",
        "titre": "Loi sur l'Autorité fédérale de surveillance des marchés financiers"
    },
    "LFLP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1994/2394_2394_2394/fr",
        "titre": "Loi sur le libre passage"
    },
    "LFPr": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2002/728/fr",
        "titre": "Loi sur la formation professionnelle"
    },
    "LFSO": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2010/77/fr",
        "titre": "Loi sur la formation continue"
    },
    "LFSP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1991/2259_2259_2259/fr",
        "titre": "Loi fédérale sur la pêche"
    },
    "LFus": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2004/3/fr",
        "titre": "Loi sur la fusion"
    },
    "LGA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1995/2513/fr",
        "titre": "Loi sur le génie génétique"
    },
    "LGéo": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2008/388/fr",
        "titre": "Loi sur la géoinformation"
    },
    "LGG": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2003/705/fr",
        "titre": "Loi sur le génie génétique"
    },
    "LHand": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2003/667/fr",
        "titre": "Loi sur l'égalité pour les handicapés"
    },
    "LIFD": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1991/1184_1184_1184/fr",
        "titre": "Loi fédérale sur l'impôt fédéral direct"
    },
    "LHID": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1991/1256_1256_1256/fr",
        "titre": "Loi fédérale sur l'harmonisation des impôts directs des cantons et des communes"
    },
    "LMCFA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2006/440/fr",
        "titre": "Loi sur le Contrôle fédéral des finances"
    },
    "LMCMP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2018/732/fr",
        "titre": "Loi fédérale sur les moyens de contrainte et les mesures policières"
    },
    "LMI": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1996/1738_1738_1738/fr",
        "titre": "Loi sur le marché intérieur"
    },
    "LMP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2020/126/fr",
        "titre": "Loi fédérale sur les marchés publics"
    },
    "LMSI": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1998/1546_1546_1546/fr",
        "titre": "Loi fédérale instituant des mesures visant au maintien de la sûreté intérieure"
    },
    "LN": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2016/404/fr",
        "titre": "Loi sur la nationalité suisse"
    },
    "LPA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2008/414/fr",
        "titre": "Loi fédérale sur la protection des animaux"
    },
    "LPAC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2015/435/fr",
        "titre": "Loi sur la poste"
    },
    "LPCFam": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2011/517/fr",
        "titre": "Loi sur les prestations complémentaires cantonales pour familles et les prestations cantonales de la rente-pont"
    },
    "LPCC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2006/822/fr",
        "titre": "Loi sur les placements collectifs"
    },
    "LPCy": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2022/614/fr",
        "titre": "Loi fédérale sur la cybersécurité"
    },
    "LPE": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1984/1122_1122_1122/fr",
        "titre": "Loi sur la protection de l'environnement"
    },
    "LPers": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2001/123/fr",
        "titre": "Loi sur le personnel de la Confédération"
    },
    "LPGA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2001/145/fr",
        "titre": "Loi fédérale sur la partie générale du droit des assurances sociales"
    },
    "LPM": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1993/274_274_274/fr",
        "titre": "Loi sur la protection des marques"
    },
    "LPMA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2001/118/fr",
        "titre": "Loi fédérale sur la procréation médicalement assistée"
    },
    "LPMed": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2007/537/fr",
        "titre": "Loi sur les professions médicales"
    },
    "LPN": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2004/81/fr",
        "titre": "Loi fédérale sur la protection de la nature et du paysage"
    },
    "LPP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1983/797_797_797/fr",
        "titre": "Loi fédérale sur la prévoyance professionnelle vieillesse, survivants et invalidité"
    },
    "LRD": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2006/678/fr",
        "titre": "Loi sur la radio et la télévision"
    },
    "LRENS": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2017/494/fr",
        "titre": "Loi sur le renseignement"
    },
    "LRHa": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2016/365/fr",
        "titre": "Loi fédérale sur l'harmonisation des registres des habitants et d'autres registres officiels de personnes"
    },
    "LRH": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2013/617/fr",
        "titre": "Loi relative à la recherche sur l'être humain"
    },
    "LRC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1937/541_577_621/fr",
        "titre": "Loi sur la responsabilité"
    },
    "LRV": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2005/707/fr",
        "titre": "Loi sur les recueils du droit fédéral et la Feuille fédérale"
    },
    "LSA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2005/735/fr",
        "titre": "Loi sur la surveillance des assurances"
    },
    "LSFin": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2019/759/fr",
        "titre": "Loi sur les services financiers"
    },
    "LStup": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1952/241_241_245/fr",
        "titre": "Loi fédérale sur les stupéfiants et les substances psychotropes"
    },
    "LTC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1997/2187_2187_2187/fr",
        "titre": "Loi sur les télécommunications"
    },
    "LTV": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2009/680/fr",
        "titre": "Loi sur le transport de voyageurs"
    },
    "LTVA": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2009/615/fr",
        "titre": "Loi sur la TVA"
    },
    "LUD": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2009/1057/fr",
        "titre": "Loi fédérale sur l'unité de la dette"
    },
    "LUHE": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1917/223_241_241/fr",
        "titre": "Loi sur les forces hydrauliques"
    },
    "LUMV": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1993/478_478_478/fr",
        "titre": "Loi sur l'unité monétaire et les moyens de paiement"
    },
    "LUNIS": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2016/354/fr",
        "titre": "Loi sur les unités de mesure et la surveillance des instruments de mesure"
    },
    "LUrh": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1992/1288_1288_1288/fr",
        "titre": "Loi sur le droit d'auteur"
    },
    "LVC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/2005/276/fr",
        "titre": "Loi sur la surveillance des chemins de fer privés"
    },
    "LVCP": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1995/328_348_348/fr",
        "titre": "Loi fédérale sur les voies cyclables et les chemins et sentiers pédestres"
    },
    "LVLC": {
        "lien": "https://www.fedlex.admin.ch/eli/cc/1980/1411_1411_1411/fr",
        "titre": "Loi fédérale sur les fonds de placement"
    }
}


    # Fonction pour obtenir le lien Fedlex pour un code de loi donné
    def get_fedlex_link(self, law_code: str, article_number: str = "") -> str:
        law = self.fedlex_links.get(law_code)
        if law:
            return f"{law.lien}#art_{article_number}" if article_number else law.lien
        return "Code de loi non trouvé"

    # Configuration des scrapers Playwright et Selenium
    playwright_timeout: int = 60000  # Timeout en millisecondes
    selenium_timeout: int = 30  # Timeout en secondes
    selenium_max_retries: int = 3
    selenium_retry_delay: int = 5  # Délai entre les tentatives en secondes

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


# Instanciation des paramètres de configuration
settings = Settings()

def get_article_content(lawCode: str, articleNumber: str) -> Optional[Dict[str, Any]]:
    """
    Fonction pour récupérer le contenu d'un article basé sur le code de loi et le numéro d'article.
    
    Args:
        lawCode (str): Code de loi (par exemple, "CO" pour Code des obligations)
        articleNumber (str): Numéro de l'article (par exemple, "266g")
    
    Returns:
        Optional[Dict[str, Any]]: Dictionnaire contenant le titre et le contenu de l'article, ou None si non trouvé.
    """
    try:
        # Construire l'URL de l'article
        url = settings.get_fedlex_link(lawCode, articleNumber)
        
        # Faire une requête GET pour récupérer le contenu de l'article
        response = requests.get(url)
        response.raise_for_status()  # Lever une exception pour les erreurs HTTP

        # Traiter la réponse (exemple simplifié, adapter selon le format réel)
        # Il faudra probablement utiliser BeautifulSoup ou lxml pour analyser le HTML
        # Ici on simule simplement une extraction
        data = response.json()  # Supposons que la réponse soit au format JSON
        title = data.get("title")
        content = data.get("content")

        return {"title": title, "content": content}

    except requests.RequestException as e:
        logger.error(f"Erreur lors de la récupération de l'article: {str(e)}")
        return None

    except ValueError:
        logger.error("Erreur de format de données reçues")
        return None

# Exemple d'utilisation
if __name__ == "__main__":
    article = get_article_content("CO", "266g")
    if article:
        print(f"Titre: {article['title']}")
        print(f"Contenu: {article['content']}")
    else:
        print("Article non trouvé.")
