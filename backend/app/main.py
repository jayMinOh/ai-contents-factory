from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
import sys

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
from app.core.database import engine
from app.models import Base
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.TEMP_DIR, "generated"), exist_ok=True)

    # Log database connection info
    db_url = settings.DATABASE_URL
    # Mask password in URL for logging
    if "@" in db_url:
        protocol_user = db_url.split("@")[0]
        host_part = db_url.split("@")[1]
        if ":" in protocol_user.split("://")[1]:
            user = protocol_user.split("://")[1].split(":")[0]
            masked_url = f"{protocol_user.split('://')[0]}://{user}:****@{host_part}"
        else:
            masked_url = db_url
    else:
        masked_url = db_url

    print(f"Starting {settings.APP_NAME}...")
    print(f"Database connection: {masked_url}")

    # Create database tables if in debug mode (development convenience)
    if settings.DEBUG:
        print("Debug mode: Creating database tables if they don't exist...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables ready.")

    yield

    # Shutdown
    print("Disposing database connection pool...")
    await engine.dispose()
    print("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered marketing video creation platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (persistent storage)
app.mount("/static", StaticFiles(directory=settings.TEMP_DIR), name="static")

# Static files for uploads (videos, etc.)
import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API Routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}
