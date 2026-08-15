from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.collectors.base import Collector, CollectorResult, SourceLimited
from src.collectors.http import Fetcher, clean_text
from src.models import JobPosting


KEYWORDS = ["comex", "commerce", "trade", "import", "export", "aduana", "customs", "logistics", "intern", "trainee"]


class ATSWatchlistCollector(Collector):
    source_name = "ATS watchlist"

    def __init__(self, config: dict):
        self.config = config
        self.fetcher = Fetcher(config["app"].get("request_timeout_seconds", 20))

    def collect(self) -> CollectorResult:
        result = CollectorResult(source=self.source_name)
        source_config = self.config.get("sources", {}).get("ats_watchlist", {})
        if not source_config.get("enabled", True):
            return result

        for page in source_config.get("pages", []):
            url = page["url"]
            try:
                html = self.fetcher.get_text(url)
                result.jobs.extend(self._parse_links(html, url, page["name"]))
            except SourceLimited as exc:
                result.limited = True
                result.errors.append(str(exc))
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{url}: {type(exc).__name__}: {exc}")
        return result

    def _parse_links(self, html: str, base_url: str, source: str) -> list[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[JobPosting] = []
        seen: set[str] = set()
        for link in soup.find_all("a", href=True):
            title = clean_text(link.get_text(" "), 160)
            href = urljoin(base_url, link["href"])
            text = clean_text((link.parent.get_text(" ") if link.parent else title), 800)
            haystack = f"{title} {href} {text}".lower()
            if href in seen or not title:
                continue
            if any(keyword in haystack for keyword in KEYWORDS) and "argentina" in haystack + base_url.lower():
                seen.add(href)
                jobs.append(
                    JobPosting(
                        title=title,
                        company=source.replace(" Jobs", "").replace(" Careers", ""),
                        location="Buenos Aires",
                        description=text,
                        source=source,
                        url=href,
                    )
                )
        return jobs[:20]
