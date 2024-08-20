# -*- coding: utf-8 -*-
import sys
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import subprocess
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketState
import re
from pprint import pformat
import nltk
from nltk.corpus import stopwords
import uvicorn
from functools import lru_cache
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration initiale
load_dotenv()
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Configuration du logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = 'app.log'
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Configuration de l'encodage
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Constantes et configuration
MAX_RETRIES = 3
RETRY_DELAY = 2
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logger.error("OPENAI_API_KEY n'est pas défini dans le fichier .env")
    sys.exit(1)

# Initialisation du client OpenAI
client = AsyncOpenAI(api_key=API_KEY)

# Variables globales
websocket_clients = []
SYSTEM_PROMPT = """
Vous êtes un expert en droit suisse, spécialisé dans l'analyse et l'interprétation des lois suisses. Votre tâche est de fournir des analyses juridiques détaillées et précises pour chaque question posée. Assurez-vous que votre réponse soit structurée, professionnelle et orientée vers l'application universitaire.

Structure de la réponse :

1. **Domaine(s) juridique(s) :** Identifiez le ou les domaines juridiques pertinents en rapport avec la question.
   Exemple : Droit de la famille, Droit civil.

2. **Articles de Loi :** Sélectionnez et listez les articles pertinents des codes suisses (CO, CP, CC, etc.) ainsi que d'autres lois fédérales, en rapport avec la question
   - Utilisez le format 'art. [numéro] [code]' pour les références, par exemple 'art. 139 CP' pour le Code pénal.
   - Pour chaque article, fournissez une explication concise (1-2 phrases) de sa pertinence directe à la question posée.
   Exemple :
   - art. 139 CP : Cet article traite du vol et des sanctions applicables.

3. **Résumé :** Rédigez un résumé concis (5-7 phrases) en vous concentrant uniquement sur les aspects essentiels de la question.
   Ce résumé doit être clair et directement pertinent à la question posée.

**Remarque :** Limitez vos réponses aux éléments directement pertinents à la question. Évitez toute information superflue ou hors sujet.
"""

# Chemins d'accès aux extracteurs
beta_entscheidsuche_extractor_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'beta_entscheidsuche_extractor.py'))
fedlex_extractor_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fedlex_extractor.py'))

# Initialisation de l'application FastAPI
app = FastAPI()

# Configuration des CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des fichiers statiques
static_dir = os.path.join(os.path.dirname(__file__), '../static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Fonctions utilitaires
def load_fedlex_links() -> Dict[str, Dict[str, str]]:
    fedlex_references_file = os.path.join(static_dir, 'fedlex_references.json')
    try:
        with open(fedlex_references_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erreur lors du chargement des références Fedlex: {str(e)}")
    return {}

FEDLEX_LINKS = load_fedlex_links()

@lru_cache(maxsize=100)
def normalize_law_code(code: str) -> Optional[str]:
    code = code.upper().strip()
    code_mapping = {
        "CODE DES OBLIGATIONS": "CO",
        "CODE CIVIL": "CC",
        "CODE PÉNAL": "CP",
        "CODE DE PROCÉDURE CIVILE": "CPC",
        "CODE DE PROCÉDURE PÉNALE": "CPP",
        "CONSTITUTION FÉDÉRALE": "Cst",
        "CST": "Cst",
        "CONSTITUTION": "Cst",
    }
    for key, value in code_mapping.items():
        if code.startswith(key):
            return value
    return code if code in FEDLEX_LINKS else None

# Fonctions principales
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def analyser_contenu_gpt4(question: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]
    logger.info("Envoi de la requête à OpenAI")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0.7
        )
        logger.info("Réponse reçue de OpenAI")
        
        if response.choices and len(response.choices) > 0 and response.choices[0].message:
            return {"assistantResponse": response.choices[0].message.content}
        else:
            logger.error("La structure de la réponse de l'API est inattendue")
            return {"error": "Structure de réponse inattendue de l'API"}
    except Exception as e:
        logger.error(f"Une erreur s'est produite lors de l'analyse GPT-4 : {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def parse_gpt4_response(response: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    sections = response.split("\n\n")
    for section in sections:
        if "Domaine(s) juridique(s) :" in section:
            result["Domaines juridiques"] = section.split(":", 1)[1].strip()
        elif "Articles de Loi :" in section:
            result["Articles de Loi"] = parse_articles(section)
        elif "Résumé :" in section:
            result["Résumé"] = section.split(":", 1)[1].strip()
        elif "Principe jurisprudentiel / Arrêt de référence :" in section:
            result["Principe jurisprudentiel"] = [line.strip("- ") for line in section.split("\n")[1:] if line.strip()]
        elif "Controverse ou évolution" in section:
            result["Controverse ou évolution"] = section.split(":", 1)[1].strip()
    return result

def parse_articles(section: str) -> List[Dict[str, str]]:
    articles = []
    for line in section.split('\n')[1:]:
        match = re.match(r'\s*-\s*(?:art\.|article)\s*(\d+[a-z]?(?:-\d+[a-z]?)?)\s*(?:al\.\s*\d+)?\s*(?:du|de la)?\s*([^:]+):\s*(.+)', line.strip(), re.IGNORECASE)
        if match:
            article_number, law_name, description = match.groups()
            law_code = re.search(r'\(([^)]+)\)', law_name)
            law_code = law_code.group(1) if law_code else normalize_law_code(law_name.split()[0])
            if law_code:
                articles.append({
                    "article_number": article_number.replace(' ', ''),
                    "law_code": law_code,
                    "law_name": law_name.strip(),
                    "description": description.strip()
                })
            else:
                articles.append({"error": f"Code de loi non reconnu: {law_name}"})
        else:
            articles.append({"error": f"Format d'article non reconnu: {line.strip()}"})
    return articles

article_cache = {}

async def extract_fedlex_article(law_code: str, article_number: str) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
    cache_key = f"{law_code}-{article_number}"
    if cache_key in article_cache:
        return article_cache[cache_key]

    try:
        normalized_law_code = normalize_law_code(law_code)
        if normalized_law_code is None:
            return {"success": False, "error": f"Code de loi non reconnu: {law_code}"}

        article_numbers = range(int(article_number.split('-')[0]), int(article_number.split('-')[-1]) + 1) if '-' in article_number else [article_number]
        articles_extracted = []

        for number in article_numbers:
            number_str = str(number).replace('art.', '').strip()
            logger.info(f"Extraction de l'article {normalized_law_code} {number_str}")

            result = await run_fedlex_extractor(normalized_law_code, number_str)
            
            if result.get("success"):
                articles_extracted.append(result)
                article_cache[cache_key] = result
            else:
                articles_extracted.append({"error": result.get('error', 'Erreur inconnue')})

        return {"success": True, "articles": articles_extracted}
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de l'article {law_code} {article_number} : {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": f"Erreur lors de l'extraction: {str(e)}"}

async def run_fedlex_extractor(law_code: str, article_number: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, 
            lambda: subprocess.run(
                [sys.executable, fedlex_extractor_path, law_code, article_number],
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )
        )
    
    if result.returncode == 0 and result.stdout.strip():
        return json.loads(result.stdout)
    else:
        return {"success": False, "error": result.stderr or "Erreur inconnue lors de l'extraction"}

async def extract_jurisprudence(keywords: List[str]) -> List[Dict[str, Any]]:
    tasks = [fetch_jurisprudence(keyword) for keyword in keywords]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jurisprudence_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Erreur lors de l'extraction de la jurisprudence : {str(result)}")
        elif result:
            jurisprudence_results.extend(result)
    return jurisprudence_results

async def fetch_jurisprudence(keyword: str) -> List[Dict[str, Any]]:
    try:
        logger.info(f"Extraction pour le mot-clé: {keyword}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                [sys.executable, beta_entscheidsuche_extractor_path, keyword],
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        else:
            logger.error(f"Erreur lors de l'extraction de la jurisprudence pour {keyword}: {result.stderr}")
            return []
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'extraction de la jurisprudence pour {keyword}: {str(e)}")
        logger.error(traceback.format_exc())
        return []

async def process_question(question: str, keywords: List[str]) -> Dict[str, Any]:
    try:
        logger.info(f"Traitement de la question : {question}")

        analysis_result = await analyser_contenu_gpt4(question)

        if "error" in analysis_result:
            return {"error": analysis_result["error"]}

        if not analysis_result or "assistantResponse" not in analysis_result:
            return {"error": "Erreur lors de l'analyse GPT-4"}

        parsed_result = parse_gpt4_response(analysis_result["assistantResponse"])
        logger.info(f"Résultat parsé: {pformat(parsed_result)}")

        articles_to_extract = [(article['law_code'], article['article_number']) for article in parsed_result.get('Articles de Loi', []) if 'error' not in article]
        articles_tasks = [extract_fedlex_article(law_code, article_number) for law_code, article_number in articles_to_extract]
        articles = await asyncio.gather(*articles_tasks, return_exceptions=True)

        formatted_articles = []
        for article in articles:
            if not isinstance(article, Exception) and 'articles' in article:
                for art in article['articles']:
                    formatted_articles.append({
                        "law_code": art.get("law_code"),
                        "article_number": art.get("article_number"),
                        "title": art.get("title", "Sans titre"),
                        "content": art.get("content", "Contenu non disponible")
                    })

        jurisprudence = await extract_jurisprudence(keywords)

        result = {
            "assistantResponse": analysis_result["assistantResponse"],
            "analysis": parsed_result,
            "articles": formatted_articles,
            "jurisprudence": jurisprudence
        }

        return result
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement de la question : {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur interne du serveur: {str(e)}"}

# Routes FastAPI
@app.post("/api/process")
async def process_request(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        question = data.get("question", "")
        keywords = data.get("keywords", [])

        if not question:
            raise HTTPException(status_code=400, detail="Question non fournie")

        if not keywords:
            raise HTTPException(status_code=400, detail="Mots-clés non fournis")

        result = await process_question(question, keywords)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return JSONResponse(content=result)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement de la requête : {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": f"Erreur interne du serveur: {str(e)}"}, status_code=500)

@app.post("/api/fetch-article")
async def fetch_article(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        law_code = data.get("lawCode")
        article_number = data.get("articleNumber")

        if not law_code or not article_number:
            raise HTTPException(status_code=400, detail="Code de loi et numéro d'article requis")

        article_result = await extract_fedlex_article(law_code, article_number)

        if not article_result["success"]:
            return JSONResponse(content={"error": article_result["error"]}, status_code=404)

        formatted_articles = [
            {
                "law_code": art.get("law_code"),
                "article_number": art.get("article_number"),
                "title": art.get("title", "Sans titre"),
                "content": art.get("content", "Contenu non disponible")
            }
            for art in article_result["articles"]
        ]

        return JSONResponse(content={"success": True, "articles": formatted_articles})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'article : {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": f"Erreur interne du serveur: {str(e)}"}, status_code=500)

@app.get("/api/extracted_data")
async def get_extracted_data() -> JSONResponse:
    try:
        extracted_data = [{"field1": "value1", "field2": "value2"}, {"field1": "value3", "field2": "value4"}]
        
        if not extracted_data:
            return JSONResponse(content={"status": "error", "message": "Aucune donnée extraite disponible"}, status_code=404)

        return JSONResponse(content={"status": "success", "data": extracted_data})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données extraites : {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"status": "error", "message": f"Erreur interne du serveur: {str(e)}"}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, 'index.html')
    return FileResponse(index_path)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    return FileResponse(favicon_path)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    try:
        async for data in websocket.iter_json():
            question = data.get("question", "")
            keywords = data.get("keywords", [])
            if not question:
                await websocket.send_json({"type": "error", "data": "Question non fournie"})
                continue

            if not keywords:
                await websocket.send_json({"type": "error", "data": "Mots-clés non fournis"})
                continue

            try:
                result = await process_question(question, keywords)
                
                # Envoyer la réponse de l'assistant
                await websocket.send_json({"type": "assistantResponse", "data": result["assistantResponse"]})
                
                # Envoyer l'analyse
                await websocket.send_json({"type": "analysis", "data": result["analysis"]})
                
                # Envoyer les articles
                for article in result["articles"]:
                    await websocket.send_json({"type": "article", "data": article})
                
                # Envoyer la jurisprudence
                for jurisprudence in result["jurisprudence"]:
                    await websocket.send_json({"type": "jurisprudence", "data": jurisprudence})
                
                await websocket.send_json({"type": "complete", "data": "Traitement terminé"})
            except Exception as e:
                logger.error(f"Erreur lors du traitement de la question: {str(e)}")
                await websocket.send_json({"type": "error", "data": str(e)})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Erreur WebSocket: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        websocket_clients.remove(websocket)

# Point d'entrée principal
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)



























































































































































