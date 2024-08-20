# -*- coding: utf-8 -*-
import logging
import time
import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    status,
    BackgroundTasks,
    Query,
)
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError  # For database error handling

# Import des modules et fonctions nécessaires
from .fedlex_extractor import extract_fedlex_article
from .config import Settings
from .main import process_question  # Assurez-vous que cette fonction est correctement importée
from .database import get_db, ExtractedData  # Exemple de module de base de données
from .parsers import JSONParser, HTMLParser  # Import des parsers pour JSON et HTML

# Initialiser le routeur et les paramètres de configuration
router = APIRouter()
settings = Settings()

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Modèles Pydantic pour la validation des données
class QuestionRequest(BaseModel):
    question: str

class ArticleRequest(BaseModel):
    lawCode: str
    articleNumber: str

class JurisprudenceResponse(BaseModel):
    id: int
    title: str
    content: str

# Middleware pour ajouter le temps de traitement aux en-têtes de réponse
@router.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Instance de sécurité OAuth2 pour l'authentification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Gestionnaire d'erreurs personnalisé pour HTTPException
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

class LegalRoutes:
    """
    Classe regroupant les routes liées aux fonctionnalités légales.
    """

    @router.get("/health", tags=["system"])
    async def health_check():
        return {"status": "healthy"}

    @router.post("/api/process", response_model=Dict[str, Any], tags=["legal"])
    async def process_request(
        request: QuestionRequest, db: Session = Depends(get_db)
    ):
        try:
            result = await process_question(request.question, db=db)
            return JSONResponse(content=result)
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    @router.post("/api/fetch-article", tags=["legal"])
    async def fetch_article(request: ArticleRequest) -> JSONResponse:
        try:
            article_result = extract_fedlex_article(
                request.lawCode, request.articleNumber
            )

            if not article_result["success"]:
                error_message = article_result.get("error", "Article non trouvé")
                logger.error(f"Erreur lors de la récupération de l'article : {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=error_message
                )

            return JSONResponse(
                content={
                    "success": True,
                    "law_code": article_result["law_code"],
                    "article_number": article_result["article_number"],
                    "title": article_result["title"],
                    "content": article_result["content"],
                }
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'article : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne du serveur",
            )

    @router.websocket("/ws", tags=["real-time"])
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                question = data.get("question", "")
                if not question:
                    await websocket.send_json({"type": "error", "data": "Question non fournie"})
                    continue

                result = await process_question(question)
                if "error" in result:
                    await websocket.send_json({"type": "error", "data": result["error"]})
                else:
                    await websocket.send_json({"type": "result", "data": result})
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Erreur WebSocket: {str(e)}")
            await websocket.close()

    @router.get("/api/jurisprudence", tags=["legal"])
    async def get_jurisprudence(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
    ):
        try:
            all_jurisprudence = await fetch_all_jurisprudence()
            start = (page - 1) * limit
            end = start + limit
            paginated_data = all_jurisprudence[start:end]
            return JSONResponse(
                content={"page": page, "limit": limit, "data": paginated_data}
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la jurisprudence : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne du serveur",
            )

    @router.get(
        "/api/jurisprudence/{jurisprudence_id}",
        response_model=JurisprudenceResponse,
        tags=["legal"],
    )
    async def get_jurisprudence_detail(jurisprudence_id: int):
        try:
            jurisprudence = await fetch_jurisprudence_by_id(jurisprudence_id)
            if not jurisprudence:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Jurisprudence non trouvée",
                )
            return jurisprudence
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la jurisprudence : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne du serveur",
            )

    @router.get("/api/protected", tags=["security"])
    async def protected_route(token: str = Depends(oauth2_scheme)):
        try:
            user = await authenticate_user(token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            return JSONResponse(content={"message": "Access granted", "user": user})
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Erreur d'authentification : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne du serveur",
            )

    @router.post("/api/long-process", tags=["background"])
    async def start_long_process(background_tasks: BackgroundTasks):
        background_tasks.add_task(long_running_task)
        return {"message": "Task started"}

    @router.get("/api/cached-data", tags=["cache"])
    async def get_cached_data():
        try:
            data = await fetch_data_to_cache()
            return JSONResponse(content={"data": data})
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données mises en cache : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne du serveur",
            )

    @router.get("/api/extracted_data", tags=["data"])
    async def get_extracted_data(db: Session = Depends(get_db)):
        try:
            extracted_data = db.query(ExtractedData).all()
            data = [
                {"id": item.id, "title": item.title, "content": item.content}
                for item in extracted_data
            ]
            return JSONResponse(content={"status": "success", "data": data})
        except SQLAlchemyError as e:
            logger.error(f"Erreur lors de la requête de la base de données: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de l'accès à la base de données",
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données extraites : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur interne du serveur",
            )

    # Ajout des routes pour les parsers
    @router.post("/parse-json", tags=["parsing"])
    def parse_json(data: str):
        parser = JSONParser()
        parsed_data = parser.parse(data)
        return parsed_data

    @router.post("/parse-html", tags=["parsing"])
    def parse_html(data: str):
        parser = HTMLParser()
        parsed_data = parser.parse(data)
        return parsed_data

    # Ajout de la route pour la gestion des sessions
    @router.get("/session-data", tags=["session"])
    def get_session_data(request: Request):
        return {"session_data": request.session.get("user_data")}

# Tests unitaires pour les endpoints
from fastapi.testclient import TestClient
client = TestClient(router)

def test_process_request():
    response = client.post("/api/process", json={"question": "Test question"})
    assert response.status_code == 200
    assert "assistantResponse" in response.json()

def test_fetch_article():
    response = client.post(
        "/api/fetch-article", json={"lawCode": "CC", "articleNumber": "1"}
    )
    assert response.status_code == 200
    assert "title" in response.json()

def test_get_extracted_data():
    response = client.get("/api/extracted_data")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert isinstance(response.json()["data"], list)

