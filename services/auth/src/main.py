"""
Auth Service - Authentication and User Management
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import settings
from src.models import init_db
from src.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup/shutdown"""
    print("Initializing database...")
    await init_db()
    print("Database initialized!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Cloud Storage Auth Service",
    description="Authentication and user management service for Cloud File Storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Note: CORS is handled by the API Gateway (Caddy).
# If running standalone, you may need to add CORSMiddleware here.

# Include main API router
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
