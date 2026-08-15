from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.classifiers.rules import classify_experience, classify_relevance
from src.collectors import (
    ATSWatchlistCollector,
    IndeedPublicCollector,
    JobintCollector,
    KnownPublicJobsCollector,
    LinkedInPublicCollector,
)
from src.config import load_config
from src.database.sqlite_store import SQLiteStore
from src.deduplication.dedupe import assign_duplicate_hash
from src.geolocation import estimate_route_for_job
from src.notifications import notify
from src.reports import write_report
from src.scoring.score import score_job


def main() -> int:
    config = load_config()
    _setup_logging(config)
    started_at = datetime.now().isoformat(timespec="seconds")
    logging.info("starting radar run")

    collectors = [
        KnownPublicJobsCollector(config),
        LinkedInPublicCollector(config),
        ATSWatchlistCollector(config),
        JobintCollector(config),
        IndeedPublicCollector(config),
    ]
    collected = []
    source_summary = []
    for collector in collectors:
        result = collector.collect()
        collected.extend(result.jobs)
        source_summary.append(
            {
                "source": result.source,
                "jobs": len(result.jobs),
                "errors": len(result.errors),
                "limited": result.limited,
                "error_samples": result.errors[:3],
            }
        )
        for error in result.errors[:10]:
            logging.warning("%s: %s", result.source, error)

    accepted, rejected_experience, rejected_distance = _evaluate(config, collected)

    store = SQLiteStore(config["app"]["database_path"])
    try:
        new_count, duplicate_count = store.upsert_jobs(collected)
        jobs_for_report = store.list_jobs(include_rejected=False)
        run = {
            "started_at": started_at,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "analyzed": len(collected),
            "accepted": len(accepted),
            "rejected_experience": rejected_experience,
            "rejected_distance": rejected_distance,
            "duplicates": duplicate_count,
            "errors": sum(item["errors"] for item in source_summary),
            "source_summary": source_summary,
        }
        report_path = write_report(config["app"]["reports_dir"], jobs_for_report, run, source_summary)
        run["report_path"] = report_path
        store.insert_run(run)
        notify(config, jobs_for_report[:10], report_path)
    finally:
        store.close()

    logging.info(
        "radar finished analyzed=%s accepted=%s new=%s duplicates=%s",
        len(collected),
        len(accepted),
        new_count,
        duplicate_count,
    )
    print(f"Analizados: {len(collected)}")
    print(f"Aceptados: {len(accepted)}")
    print(f"Nuevos en DB: {new_count}")
    print(f"Duplicados: {duplicate_count}")
    print(f"Reporte: {report_path}")
    return 0


def _evaluate(config: dict, jobs: list) -> tuple[list, int, int]:
    accepted = []
    rejected_experience = 0
    rejected_distance = 0
    app = config["app"]
    profile = config.get("candidate_profile", {})

    for job in jobs:
        text = job.merged_text()
        job.relevance_classification, relevance_reasons = classify_relevance(text)
        job.experience_classification, experience_reason = classify_experience(text)
        job.experience_required_text = experience_reason
        route = estimate_route_for_job(job, app["reference_location"])
        job.latitude = route.latitude
        job.longitude = route.longitude
        job.distance_km = route.distance_km
        job.travel_minutes = route.travel_minutes
        job.travel_is_estimated = route.is_estimated
        score_job(job, profile)
        assign_duplicate_hash(job)

        if job.status == "EXPIRED":
            job.rejection_reasons.append("Aviso vencido o sin postulaciones abiertas.")
        if job.relevance_classification == "UNRELATED":
            job.rejection_reasons.extend(relevance_reasons)
        if job.experience_classification == "REQUIERE_EXPERIENCIA":
            rejected_experience += 1
            job.rejection_reasons.append(experience_reason)
        if job.travel_minutes is not None and job.travel_minutes > app["max_travel_minutes"]:
            rejected_distance += 1
            job.rejection_reasons.append(
                f"Viaje estimado {int(job.travel_minutes)} min, supera {app['max_travel_minutes']} min."
            )
        if job.score < app["min_score"]:
            job.rejection_reasons.append(f"Score {job.score}, menor al minimo {app['min_score']}.")

        if job.rejection_reasons:
            if job.status != "EXPIRED":
                job.status = "REJECTED"
        else:
            job.status = "NEW"
            accepted.append(job)
    return accepted, rejected_experience, rejected_distance


def _setup_logging(config: dict) -> None:
    logs_dir = Path(config["app"]["logs_dir"])
    logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=logs_dir / "radar.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


if __name__ == "__main__":
    raise SystemExit(main())
