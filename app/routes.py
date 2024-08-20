# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .fedlex_extractor import extract_fedlex_article
from .config import Settings
from .main import process_question
from .database import get_db, ExtractedData
from .auth import verify_token, get_current_user
from .jurisprudence import get_jurisprudence_paginated, get_jurisprudence_by_id
from .cache import get_cached_data, update_cache

router = APIRouter()
settings = Settings()

logger = logging.getLogger(__name__)

class QuestionRequest(BaseModel):
    question: str
    keywords: List[str] = []

class ArticleRequest(BaseModel):
    lawCode: str
    articleNumber: str

class JurisprudenceResponse(BaseModel):
    id: int
    title: str
    content: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@router.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy"}

@router.post("/api/process", response_model=Dict[str, Any], tags=["legal"])
async def process_request(request: QuestionRequest, db: Session = Depends(get_db)):
    try:
        result = await process_question(request.question, request.keywords, db)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/api/fetch-article", tags=["legal"])
async def fetch_article(request: ArticleRequest) -> JSONResponse:
    try:
        article_result = extract_fedlex_article(request.lawCode, request.articleNumber)
        if not article_result["success"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=article_result.get("error", "Article non trouvé"))
        return JSONResponse(content=article_result)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'article : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "")
            keywords = data.get("keywords", [])
            if not question:
                await websocket.send_json({"type": "error", "data": "Question non fournie"})
                continue
            result = await process_question(question, keywords)
            await websocket.send_json({"type": "result", "data": result})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Erreur WebSocket: {str(e)}")
        await websocket.close()

@router.get("/api/jurisprudence", tags=["legal"])
async def get_jurisprudence(page: int = 1, limit: int = 10):
    try:
        jurisprudence, total = await get_jurisprudence_paginated(page, limit)
        return JSONResponse(content={"page": page, "limit": limit, "total": total, "data": jurisprudence})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la jurisprudence : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur")

@router.get("/api/jurisprudence/{jurisprudence_id}", response_model=JurisprudenceResponse, tags=["legal"])
async def get_jurisprudence_detail(jurisprudence_id: int):
    try:
        jurisprudence = await get_jurisprudence_by_id(jurisprudence_id)
        if not jurisprudence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jurisprudence non trouvée")
        return jurisprudence
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la jurisprudence : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur")

@router.get("/api/protected", tags=["security"])
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        user = await get_current_user(token)
        return JSONResponse(content={"message": "Access granted", "user": user})
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erreur d'authentification : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur")

@router.post("/api/long-process", tags=["background"])
async def start_long_process(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_cache)
    return {"message": "Mise à jour du cache démarrée"}

@router.get("/api/cached-data", tags=["cache"])
async def get_cached_data_endpoint():
    try:
        data = await get_cached_data()
        return JSONResponse(content={"data": data})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données mises en cache : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur")

@router.get("/api/extracted_data", tags=["data"])
async def get_extracted_data(db: Session = Depends(get_db)):
    try:
        extracted_data = db.query(ExtractedData).all()
        data = [{"id": item.id, "title": item.title, "content": item.content} for item in extracted_data]
        return JSONResponse(content={"status": "success", "data": data})
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la requête de la base de données: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de l'accès à la base de données")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données extraites : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur")