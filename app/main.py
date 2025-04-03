from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import settings
from app.api.v1.endpoints import memories
from app.core.middleware import auth_middleware
from app.api import auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend build directory
frontend_build = Path(__file__).parent.parent / "frontend" / "build"
app.mount("/static", StaticFiles(directory=str(frontend_build / "static")), name="static")

# Include routers with API prefix
app.include_router(memories.router, prefix=f"{settings.API_V1_STR}/memories", tags=["memories"])

# Add authentication middleware
app.middleware("http")(auth_middleware)

# Include auth routes
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth")

@app.get("/")
async def root():
    return FileResponse(str(frontend_build / "index.html"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # Don't handle API routes here
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Try to serve the requested path from the frontend build
    file_path = frontend_build / full_path
    if file_path.exists():
        return FileResponse(str(file_path))
    # If the file doesn't exist, serve index.html for client-side routing
    return FileResponse(str(frontend_build / "index.html")) 