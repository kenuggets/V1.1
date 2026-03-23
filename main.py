import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from database import init_db
from routers import user, application
from routers import discover, build, prepare, gamification, testimonials

app = FastAPI(title="AI Career Assistant", version="2.0.0")


@app.on_event("startup")
async def startup():
    init_db()


# Core routers
app.include_router(user.router)
app.include_router(application.router)

# New module routers
app.include_router(discover.router)
app.include_router(build.router)
app.include_router(prepare.router)
app.include_router(gamification.router)
app.include_router(testimonials.router)

# Serve frontend
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
