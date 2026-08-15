from __future__ import annotations

import re

import httpx

from src.collectors.base import SourceLimited


LIMIT_PATTERNS = [
    "captcha",
    "cloudflare",
    "cf-browser-verification",
    "verify you are human",
    "security check",
    "unusual traffic",
    "access denied",
    "pardon the interruption",
]


class Fetcher:
    def __init__(self, timeout_seconds: int = 20):
        self.timeout_seconds = timeout_seconds
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
            },
        )

    def get_text(self, url: str) -> str:
        response = self.client.get(url)
        text = response.text or ""
        lowered = text.lower()
        if response.status_code in {401, 403, 429} or any(token in lowered for token in LIMIT_PATTERNS):
            raise SourceLimited(f"{response.status_code} limited by source: {url}")
        response.raise_for_status()
        return text


def clean_text(text: str, max_len: int = 2400) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    return compact[:max_len]
