from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import checkins, goals, tasks
from app.config import get_settings
from app.core.logging import logger
from app.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not settings.has_ai_configured:
        logger.warning(
            "OLLAMA_BASE_URL is not set. The API will start, but any endpoint "
            "that calls the AI service will return a 503 until it is configured."
        )
    yield


app = FastAPI(title="NextStep AI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(goals.router)
app.include_router(tasks.router)
app.include_router(checkins.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "ai_configured": settings.has_ai_configured}
