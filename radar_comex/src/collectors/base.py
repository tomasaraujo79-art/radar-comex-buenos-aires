from __future__ import annotations

from dataclasses import dataclass, field

from src.models import JobPosting


class SourceLimited(RuntimeError):
    """Raised when a public source asks for CAPTCHA/login or blocks automated reads."""


@dataclass
class CollectorResult:
    source: str
    jobs: list[JobPosting] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    limited: bool = False


class Collector:
    source_name = "Unknown"

    def collect(self) -> CollectorResult:
        raise NotImplementedError
