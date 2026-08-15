from __future__ import annotations

import hashlib
import re

from src.classifiers.rules import normalize
from src.models import JobPosting


def canonical_key(job: JobPosting) -> str:
    title = re.sub(r"\b(jr|junior|sr|senior|semi senior|ssr)\b", "", normalize(job.title))
    title = re.sub(r"\s+", " ", title).strip()
    company = normalize(job.company)
    location = normalize(job.location)
    return "|".join([title, company, location])[:300]


def assign_duplicate_hash(job: JobPosting) -> None:
    key = canonical_key(job)
    if not key.replace("|", "").strip() and job.url:
        key = normalize(job.url)
    job.duplicate_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
