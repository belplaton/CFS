"""
Preview Service - generated previews are not enabled yet.

Browser-native previews for images/PDF/text are currently handled in
the frontend via authenticated file downloads. This service keeps its
routes explicit so API docs reflect reality instead of commented TODOs.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


app = FastAPI(
    title="Cloud Storage Preview Service",
    description="File preview generation service for Cloud File Storage",
    version="1.0.0",
    docs_url="/docs/preview",
    redoc_url="/redoc/preview",
    openapi_url="/openapi/preview.json",
)

# CORS middleware - fixed for credentials with specific origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "preview"}


@app.get("/api/preview/")
async def root():
    """Root endpoint"""
    return {
        "message": "Preview Service is running",
        "version": "1.0.0",
        "generated_previews_enabled": False,
        "note": "Use direct file download for browser-native preview types.",
    }

def _generated_preview_not_enabled() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Generated previews are not enabled yet. "
            "Use /api/files/{id}/download for browser-native preview types."
        ),
    )


@app.get("/api/preview/{file_id}")
async def get_preview(file_id: str):
    raise _generated_preview_not_enabled()


@app.get("/api/preview/{file_id}/thumbnail")
async def get_thumbnail(file_id: str):
    raise _generated_preview_not_enabled()


@app.post("/api/preview/{file_id}/generate")
async def generate_preview(file_id: str):
    raise _generated_preview_not_enabled()


@app.delete("/api/preview/{file_id}")
async def delete_preview(file_id: str):
    raise _generated_preview_not_enabled()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
