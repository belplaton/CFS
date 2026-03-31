"""
Auth Service - Authentication and User Management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


app = FastAPI(
    title="Cloud Storage Auth Service",
    description="Authentication and user management service for Cloud File Storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - fixed for credentials with specific origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}


@app.get("/api/auth/")
async def root():
    """Root endpoint"""
    return {"message": "Auth Service is running", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
