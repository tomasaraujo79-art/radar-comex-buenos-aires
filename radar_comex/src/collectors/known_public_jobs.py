from __future__ import annotations

from bs4 import BeautifulSoup

from src.collectors.base import Collector, CollectorResult, SourceLimited
from src.collectors.http import Fetcher, clean_text
from src.models import JobPosting


EXPIRED_MARKERS = [
    "ya no se aceptan solicitudes",
    "no longer accepting applications",
    "job is no longer available",
    "puesto ya no esta disponible",
]


class KnownPublicJobsCollector(Collector):
    source_name = "Known public jobs"

    def __init__(self, config: dict):
        self.config = config
        self.fetcher = Fetcher(config["app"].get("request_timeout_seconds", 20))

    def collect(self) -> CollectorResult:
        source_config = self.config.get("sources", {}).get("known_public_jobs", {})
        result = CollectorResult(source=self.source_name)
        if not source_config.get("enabled", True):
            return result

        for item in source_config.get("jobs", []):
            job = JobPosting(
                title=item.get("title", ""),
                company=item.get("company", ""),
                location=item.get("location", ""),
                url=item.get("url", ""),
                source=item.get("source", self.source_name),
                description=item.get("description", ""),
            )
            try:
                html = self.fetcher.get_text(job.url)
                soup = BeautifulSoup(html, "html.parser")
                page_text = clean_text(soup.get_text(" "))
                meta_description = ""
                meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
                    "meta", attrs={"property": "og:description"}
                )
                if meta and meta.get("content"):
                    meta_description = clean_text(meta["content"])
                if meta_description or page_text:
                    job.description = clean_text(" ".join([job.description, meta_description, page_text]))
                if any(marker in page_text.lower() for marker in EXPIRED_MARKERS):
                    job.status = "EXPIRED"
                    job.rejection_reasons.append("El sitio publico indica que el aviso ya no acepta solicitudes.")
            except SourceLimited as exc:
                result.limited = True
                result.errors.append(str(exc))
                job.description = clean_text(
                    job.description
                    + " Fuente limitada por login/CAPTCHA; se conserva como pista para revision manual."
                )
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{job.url}: {type(exc).__name__}: {exc}")
            result.jobs.append(job)
        return result
