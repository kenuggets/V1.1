import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from database import init_db
from routers import cv, email, interview, application, user

app = FastAPI(title="AI Career Assistant", version="1.0.0")

# Initialise database on startup
@app.on_event("startup")
async def startup():
    init_db()


# Register all bot routers
app.include_router(user.router)
app.include_router(cv.router)
app.include_router(email.router)
app.include_router(interview.router)
app.include_router(application.router)

# Serve frontend static files
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(frontend_dir / "index.html"))


@app.get("/{page}.html")
async def page(page: str):
    file_path = frontend_dir / f"{page}.html"
    if file_path.exists():
        return FileResponse(str(file_path))
    return FileResponse(str(frontend_dir / "index.html"))
