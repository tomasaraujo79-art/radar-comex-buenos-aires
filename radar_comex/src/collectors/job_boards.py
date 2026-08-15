from __future__ import annotations

from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from src.collectors.base import Collector, CollectorResult, SourceLimited
from src.collectors.http import Fetcher, clean_text
from src.models import JobPosting


class LinkedInPublicCollector(Collector):
    source_name = "LinkedIn public search"

    def __init__(self, config: dict):
        self.config = config
        self.fetcher = Fetcher(config["app"].get("request_timeout_seconds", 20))

    def collect(self) -> CollectorResult:
        source_config = self.config.get("sources", {}).get("linkedin_public", {})
        result = CollectorResult(source=self.source_name)
        if not source_config.get("enabled", True):
            return result

        queries = self.config.get("search", {}).get("queries", [])
        for query in queries:
            url = (
                "https://ar.linkedin.com/jobs/search?"
                f"keywords={quote_plus(query)}&location=Buenos%20Aires%20y%20alrededores&f_E=1%2C2"
            )
            try:
                html = self.fetcher.get_text(url)
                result.jobs.extend(self._parse_search(html, url))
            except SourceLimited as exc:
                result.limited = True
                result.errors.append(str(exc))
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{url}: {type(exc).__name__}: {exc}")
        return result

    def _parse_search(self, html: str, base_url: str) -> list[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobPosting] = []
        cards = soup.select("li, div.base-card, div.job-search-card")
        for card in cards:
            href = ""
            link = card.select_one("a[href*='/jobs/view/']")
            if link and link.get("href"):
                href = link["href"].split("?")[0]
            if not href:
                continue
            title_el = card.select_one(".base-search-card__title, h3, a")
            company_el = card.select_one(".base-search-card__subtitle, h4")
            location_el = card.select_one(".job-search-card__location, .job-result-card__location")
            title = clean_text(title_el.get_text(" ") if title_el else link.get_text(" "), 160)
            if not title:
                continue
            jobs.append(
                JobPosting(
                    title=title,
                    company=clean_text(company_el.get_text(" ") if company_el else "", 120),
                    location=clean_text(location_el.get_text(" ") if location_el else "Buenos Aires y alrededores", 120),
                    description=clean_text(card.get_text(" ")),
                    source="LinkedIn",
                    url=urljoin(base_url, href),
                )
            )
        return jobs


class JobintCollector(Collector):
    source_name = "Bumeran/ZonaJobs"

    def __init__(self, config: dict):
        self.config = config
        self.fetcher = Fetcher(config["app"].get("request_timeout_seconds", 20))

    def collect(self) -> CollectorResult:
        result = CollectorResult(source=self.source_name)
        source_config = self.config.get("sources", {}).get("jobint", {})
        if not source_config.get("enabled", True):
            return result

        for board in source_config.get("boards", []):
            for query in self.config.get("search", {}).get("queries", [])[:4]:
                slug = quote_plus(query).replace("+", "-")
                url = f"{board['base_url'].rstrip('/')}/empleos-{slug}.html"
                try:
                    html = self.fetcher.get_text(url)
                    result.jobs.extend(_parse_generic_job_links(html, url, board["name"]))
                except SourceLimited as exc:
                    result.limited = True
                    result.errors.append(str(exc))
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"{url}: {type(exc).__name__}: {exc}")
        return result


class IndeedPublicCollector(Collector):
    source_name = "Indeed public search"

    def __init__(self, config: dict):
        self.config = config
        self.fetcher = Fetcher(config["app"].get("request_timeout_seconds", 20))

    def collect(self) -> CollectorResult:
        result = CollectorResult(source=self.source_name)
        source_config = self.config.get("sources", {}).get("indeed_public", {})
        if not source_config.get("enabled", True):
            return result

        for query in self.config.get("search", {}).get("queries", [])[:4]:
            url = f"https://ar.indeed.com/jobs?q={quote_plus(query)}&l=Buenos+Aires"
            try:
                html = self.fetcher.get_text(url)
                result.jobs.extend(_parse_generic_job_links(html, url, "Indeed"))
            except SourceLimited as exc:
                result.limited = True
                result.errors.append(str(exc))
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{url}: {type(exc).__name__}: {exc}")
        return result


def _parse_generic_job_links(html: str, base_url: str, source: str) -> list[JobPosting]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[JobPosting] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        text = clean_text(link.get_text(" "), 180)
        href = urljoin(base_url, link["href"])
        lowered = " ".join([text.lower(), href.lower()])
        if not text or href in seen:
            continue
        if any(token in lowered for token in ["comex", "comercio", "import", "export", "aduana", "logistica"]):
            seen.add(href)
            jobs.append(
                JobPosting(
                    title=text,
                    location="Buenos Aires",
                    description=clean_text(link.parent.get_text(" ") if link.parent else text),
                    source=source,
                    url=href,
                )
            )
    return jobs[:25]
