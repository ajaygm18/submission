from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import create_db_and_tables
from src.routers import attendance, auth, batches, monitoring, sessions, summaries

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="SkillBridge Attendance API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(summaries.router)
app.include_router(monitoring.router)
