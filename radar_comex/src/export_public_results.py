from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from src.config import load_config
from src.database.sqlite_store import SQLiteStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", required=True)
    args = parser.parse_args()

    config = load_config()
    store = SQLiteStore(config["app"]["database_path"])
    try:
        jobs = [
            _public_job(job)
            for job in store.list_jobs(include_rejected=False)
            if _is_direct_application_url(job.get("url", ""))
        ]
        latest = _public_run(store.latest_run())
    finally:
        store.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reference_location": config["app"]["reference_location"],
        "max_travel_minutes": config["app"]["max_travel_minutes"],
        "latest_run": latest,
        "jobs": jobs,
    }

    site_dir = Path(args.site_dir)
    public_dir = site_dir / "public"
    app_dir = site_dir / "app"
    public_dir.mkdir(parents=True, exist_ok=True)
    app_dir.mkdir(parents=True, exist_ok=True)
    (public_dir / "jobs.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (app_dir / "jobs-data.ts").write_text(
        "export const radarData = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + " as const;\n",
        encoding="utf-8",
    )
    print(f"Exported {len(jobs)} jobs to {site_dir}")
    return 0


def _public_job(job: dict) -> dict:
    return {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "source": job.get("source", ""),
        "url": job.get("url", ""),
        "score": job.get("score", 0),
        "travel_minutes": job.get("travel_minutes"),
        "distance_km": job.get("distance_km"),
        "experience": job.get("experience_classification", ""),
        "relevance": job.get("relevance_classification", ""),
        "description": job.get("description", ""),
        "reasons": [item.get("reason", "") for item in job.get("score_explanation", [])],
    }


def _is_direct_application_url(url: str) -> bool:
    lowered = (url or "").lower()
    if not lowered.startswith("http"):
        return False
    return "/jobs/search" not in lowered and "keywords=" not in lowered


def _public_run(run: dict | None) -> dict | None:
    if not run:
        return None
    return {
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "analyzed": run.get("analyzed", 0),
        "accepted": run.get("accepted", 0),
        "rejected_experience": run.get("rejected_experience", 0),
        "rejected_distance": run.get("rejected_distance", 0),
        "duplicates": run.get("duplicates", 0),
        "errors": run.get("errors", 0),
    }


if __name__ == "__main__":
    raise SystemExit(main())
