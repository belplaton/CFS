"""
File Service Stub - Minimal FastAPI mock for development
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid
import os

# ===========================================
# Configuration
# ===========================================

HOST = os.getenv("FILE_SERVICE_HOST", "0.0.0.0")
PORT = int(os.getenv("FILE_SERVICE_PORT", "8082"))

# ===========================================
# Models
# ===========================================

class BrowserItemKind(str):
    FOLDER = "Folder"
    FILE = "File"

class BrowserItemSummary(BaseModel):
    id: str
    name: str
    kind: str
    sizeBytes: int
    updatedAtUtc: datetime
    isShared: bool

class BrowseRootResponse(BaseModel):
    path: str
    items: List[BrowserItemSummary]

class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)

class ApiError(BaseModel):
    code: str
    message: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    service: str
    version: str
    deps: Optional[Dict[str, str]] = None

class UserSummary(BaseModel):
    id: str
    email: str
    displayName: str

# ===========================================
# Mock Data Storage
# ===========================================

# Хранилище файлов по пользователям: user_id -> [items]
files_by_user: Dict[str, List[BrowserItemSummary]] = {}

# ===========================================
# Application
# ===========================================

app = FastAPI(
    title="File Service (Stub)",
    description="Mock file service for development",
    version="0.1.0-stub"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# Helper Functions
# ===========================================

def get_seed_items() -> List[BrowserItemSummary]:
    """Создаёт тестовые данные для нового пользователя"""
    now = datetime.now(timezone.utc)
    return [
        BrowserItemSummary(
            id=str(uuid.uuid4()),
            name="Design",
            kind="Folder",
            sizeBytes=0,
            updatedAtUtc=now,
            isShared=False
        ),
        BrowserItemSummary(
            id=str(uuid.uuid4()),
            name="Network Contracts",
            kind="Folder",
            sizeBytes=0,
            updatedAtUtc=now,
            isShared=True
        ),
        BrowserItemSummary(
            id=str(uuid.uuid4()),
            name="roadmap.md",
            kind="File",
            sizeBytes=18432,
            updatedAtUtc=now,
            isShared=False
        ),
        BrowserItemSummary(
            id=str(uuid.uuid4()),
            name="screenshots.zip",
            kind="File",
            sizeBytes=2456789,
            updatedAtUtc=now,
            isShared=True
        )
    ]

def get_user_items(user_id: str) -> List[BrowserItemSummary]:
    """Получает или создаёт файлы пользователя"""
    if user_id not in files_by_user:
        files_by_user[user_id] = get_seed_items()
    return files_by_user[user_id]

def extract_user_id_from_token(token: Optional[str]) -> Optional[str]:
    """Извлекает user_id из токена (mock)"""
    if not token:
        return None
    # В mock-версии просто возвращаем фиктивный ID
    return f"user-{token[:8]}" if len(token) > 8 else "user-mock"

# ===========================================
# Endpoints
# ===========================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        service="file-service",
        version="0.1.0-stub",
        deps={
            "postgres": "mock",
            "storage-service": "mock"
        }
    )

@app.get("/api/files/root", response_model=BrowseRootResponse)
async def get_root_files(authorization: Optional[str] = Header(None)):
    """Получает корневые файлы пользователя"""
    user_id = extract_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=ApiError(
                code="auth.missing_token",
                message="Authorization header is required"
            ).model_dump()
        )
    
    items = get_user_items(user_id)
    return BrowseRootResponse(path="/", items=items)

@app.post("/api/folders", response_model=BrowseRootResponse)
async def create_folder(
    request: CreateFolderRequest,
    authorization: Optional[str] = Header(None)
):
    """Создаёт новую папку"""
    user_id = extract_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=ApiError(
                code="auth.missing_token",
                message="Authorization header is required"
            ).model_dump()
        )
    
    items = get_user_items(user_id)
    
    # Проверка на дубликат
    normalized_name = request.name.strip()
    for item in items:
        if item.kind == "Folder" and item.name.lower() == normalized_name.lower():
            raise HTTPException(
                status_code=400,
                detail=ApiError(
                    code="folders.duplicate",
                    message="A folder with this name already exists"
                ).model_dump()
            )
    
    # Создаём новую папку
    new_folder = BrowserItemSummary(
        id=str(uuid.uuid4()),
        name=normalized_name,
        kind="Folder",
        sizeBytes=0,
        updatedAtUtc=datetime.now(timezone.utc),
        isShared=False
    )
    items.append(new_folder)
    
    return BrowseRootResponse(path="/", items=items)

# ===========================================
# Main
# ===========================================

if __name__ == "__main__":
    import uvicorn
    print(f"File Service (stub) starting on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
