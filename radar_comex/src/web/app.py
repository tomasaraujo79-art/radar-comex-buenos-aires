from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import ROOT, load_config
from src.database.sqlite_store import SQLiteStore


config = load_config()
app = FastAPI(title="Radar COMEX")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/jobs")
def jobs(
    include_rejected: bool = False,
    min_score: int = Query(0, ge=0, le=100),
    q: str = "",
) -> list[dict]:
    store = SQLiteStore(config["app"]["database_path"])
    try:
        rows = store.list_jobs(include_rejected=include_rejected)
    finally:
        store.close()
    q_clean = q.strip().lower()
    filtered = []
    for row in rows:
        haystack = " ".join(str(row.get(key) or "") for key in ["title", "company", "location", "source"]).lower()
        if row.get("score", 0) >= min_score and (not q_clean or q_clean in haystack):
            filtered.append(row)
    return filtered


@app.get("/api/stats")
def stats() -> dict:
    store = SQLiteStore(config["app"]["database_path"])
    try:
        jobs = store.list_jobs(include_rejected=True)
        latest = store.latest_run()
    finally:
        store.close()
    accepted = [job for job in jobs if job["status"] not in {"REJECTED", "DUPLICATE", "EXPIRED"}]
    return {
        "total": len(jobs),
        "accepted": len(accepted),
        "rejected": len([job for job in jobs if job["status"] == "REJECTED"]),
        "expired": len([job for job in jobs if job["status"] == "EXPIRED"]),
        "top_score": max((job.get("score") or 0 for job in jobs), default=0),
        "latest_run": latest,
    }


dist = ROOT / "dashboard" / "dist"
if dist.exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str = ""):
        requested = dist / path
        if path and requested.exists() and requested.is_file():
            return FileResponse(requested)
        return FileResponse(dist / "index.html")
