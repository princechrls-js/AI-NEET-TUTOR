from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import uvicorn
from app.core.config import settings
from app.api.router import api_router

def create_data_folders():
    subjects = ["biology", "chemistry", "physics"]
    base_dirs = ["raw", "processed", "vector_store"]
    
    for base in base_dirs:
        for subject in subjects:
            path = os.path.join("app", "data", base, subject)
            os.makedirs(path, exist_ok=True)

from contextlib import asynccontextmanager
from app.db.redis_client import init_redis, close_redis
from app.services.embedding_service import _get_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    
    # Eagerly load the embedding model to avoid cold-start delays on the first query
    print("Pre-loading generating embedding model...")
    _get_model()
    
    yield
    # Shutdown
    await close_redis()

def create_app() -> FastAPI:
    # Ensure directories exist
    create_data_folders()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="FastAPI backend for AI NEET Coaching platform with subject-wise RAG.",
        lifespan=lifespan
    )
    
    from fastapi.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins for development
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
        allow_headers=["*"],  # Allows all headers
    )
    
    # Include all routers
    app.include_router(api_router)
    
    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "available_subjects": ["biology", "chemistry", "physics"],
            "endpoints": ["/auth/signup", "/auth/login", "/health", "/subjects", "/ingest/upload", "/ask", "/history", "/quiz/generate", "/users"]
        }
        
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("start_app:app", host=settings.HOST, port=settings.PORT, reload=True)
