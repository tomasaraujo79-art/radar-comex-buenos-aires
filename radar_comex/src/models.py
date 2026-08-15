from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class JobPosting:
    title: str
    company: str = ""
    description: str = ""
    location: str = ""
    modality: str = ""
    published_at: str = ""
    found_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    source: str = ""
    url: str = ""
    alternative_urls: list[str] = field(default_factory=list)
    experience_required_text: str = ""
    experience_classification: str = "NO_ESPECIFICA_EXPERIENCIA"
    relevance_classification: str = "UNKNOWN"
    score: int = 0
    score_explanation: list[dict[str, Any]] = field(default_factory=list)
    distance_km: float | None = None
    travel_minutes: float | None = None
    travel_is_estimated: bool = True
    latitude: float | None = None
    longitude: float | None = None
    status: str = "NEW"
    last_checked_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    duplicate_hash: str = ""
    rejection_reasons: list[str] = field(default_factory=list)

    def merged_text(self) -> str:
        return " ".join(
            part for part in [self.title, self.company, self.description, self.location, self.modality] if part
        )

