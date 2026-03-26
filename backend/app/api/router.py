from fastapi import APIRouter
from app.api.routes import health, subjects, ingest, ask, users, auth, history, quiz

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(ask.router, prefix="/ask", tags=["ask"])
api_router.include_router(history.router, prefix="/history", tags=["chat history"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
