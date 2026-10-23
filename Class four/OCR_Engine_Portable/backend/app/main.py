from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, ocr
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.temp_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="OCR Detection Engine",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(ocr.router, prefix="/api/v1")
