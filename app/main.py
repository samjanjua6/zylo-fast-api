from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.database import Base, engine
from .models import User
from .routers import auth, users


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Simple FastAPI User API")
app.include_router(auth.router)
app.include_router(users.router)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def home():
	return FileResponse(static_dir / "index.html")
