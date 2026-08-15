from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from src.models import JobPosting


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    description TEXT,
    location TEXT,
    modality TEXT,
    published_at TEXT,
    found_at TEXT,
    source TEXT,
    url TEXT,
    alternative_urls TEXT,
    experience_required_text TEXT,
    experience_classification TEXT,
    relevance_classification TEXT,
    score INTEGER,
    score_explanation TEXT,
    distance_km REAL,
    travel_minutes REAL,
    travel_is_estimated INTEGER,
    latitude REAL,
    longitude REAL,
    status TEXT,
    last_checked_at TEXT,
    duplicate_hash TEXT UNIQUE,
    rejection_reasons TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    finished_at TEXT,
    analyzed INTEGER,
    accepted INTEGER,
    rejected_experience INTEGER,
    rejected_distance INTEGER,
    duplicates INTEGER,
    errors INTEGER,
    report_path TEXT,
    source_summary TEXT
);
"""


class SQLiteStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def upsert_jobs(self, jobs: Iterable[JobPosting]) -> tuple[int, int]:
        new_count = 0
        duplicate_count = 0
        for job in jobs:
            existing = self.conn.execute(
                "SELECT id, alternative_urls, status FROM jobs WHERE duplicate_hash = ?",
                (job.duplicate_hash,),
            ).fetchone()
            if existing:
                duplicate_count += 1
                urls = set(json.loads(existing["alternative_urls"] or "[]"))
                if job.url:
                    urls.add(job.url)
                for url in job.alternative_urls:
                    urls.add(url)
                self.conn.execute(
                    """
                    UPDATE jobs
                    SET title = ?, company = ?, description = ?, location = ?, modality = ?,
                        published_at = ?, source = ?, url = ?,
                        alternative_urls = ?, experience_required_text = ?,
                        experience_classification = ?, relevance_classification = ?, score = ?,
                        score_explanation = ?, distance_km = ?, travel_minutes = ?,
                        travel_is_estimated = ?, latitude = ?, longitude = ?, status = ?,
                        last_checked_at = ?, rejection_reasons = ?
                    WHERE id = ?
                    """,
                    (
                        job.title,
                        job.company,
                        job.description,
                        job.location,
                        job.modality,
                        job.published_at,
                        job.source,
                        job.url,
                        json.dumps(sorted(urls), ensure_ascii=False),
                        job.experience_required_text,
                        job.experience_classification,
                        job.relevance_classification,
                        job.score,
                        json.dumps(job.score_explanation, ensure_ascii=False),
                        job.distance_km,
                        job.travel_minutes,
                        int(job.travel_is_estimated),
                        job.latitude,
                        job.longitude,
                        job.status,
                        job.last_checked_at,
                        json.dumps(job.rejection_reasons, ensure_ascii=False),
                        existing["id"],
                    ),
                )
                continue

            self.conn.execute(
                """
                INSERT INTO jobs (
                    title, company, description, location, modality, published_at, found_at,
                    source, url, alternative_urls, experience_required_text,
                    experience_classification, relevance_classification, score, score_explanation,
                    distance_km, travel_minutes, travel_is_estimated, latitude, longitude, status,
                    last_checked_at, duplicate_hash, rejection_reasons
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.title,
                    job.company,
                    job.description,
                    job.location,
                    job.modality,
                    job.published_at,
                    job.found_at,
                    job.source,
                    job.url,
                    json.dumps(job.alternative_urls, ensure_ascii=False),
                    job.experience_required_text,
                    job.experience_classification,
                    job.relevance_classification,
                    job.score,
                    json.dumps(job.score_explanation, ensure_ascii=False),
                    job.distance_km,
                    job.travel_minutes,
                    int(job.travel_is_estimated),
                    job.latitude,
                    job.longitude,
                    job.status,
                    job.last_checked_at,
                    job.duplicate_hash,
                    json.dumps(job.rejection_reasons, ensure_ascii=False),
                ),
            )
            new_count += 1
        self.conn.commit()
        return new_count, duplicate_count

    def insert_run(self, run: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO runs (
                started_at, finished_at, analyzed, accepted, rejected_experience,
                rejected_distance, duplicates, errors, report_path, source_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.get("started_at"),
                run.get("finished_at"),
                run.get("analyzed", 0),
                run.get("accepted", 0),
                run.get("rejected_experience", 0),
                run.get("rejected_distance", 0),
                run.get("duplicates", 0),
                run.get("errors", 0),
                run.get("report_path", ""),
                json.dumps(run.get("source_summary", []), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def list_jobs(self, include_rejected: bool = False) -> list[dict]:
        where = "" if include_rejected else "WHERE status NOT IN ('REJECTED', 'DUPLICATE')"
        rows = self.conn.execute(
            f"SELECT * FROM jobs {where} ORDER BY score DESC, found_at DESC"
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def latest_run(self) -> dict | None:
        row = self.conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        data = dict(row)
        data["source_summary"] = json.loads(data.get("source_summary") or "[]")
        return data

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        data = dict(row)
        for key in ["alternative_urls", "score_explanation", "rejection_reasons"]:
            data[key] = json.loads(data.get(key) or "[]")
        data["travel_is_estimated"] = bool(data.get("travel_is_estimated"))
        return data
