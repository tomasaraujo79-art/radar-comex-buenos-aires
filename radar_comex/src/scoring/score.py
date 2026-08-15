from __future__ import annotations

from datetime import datetime, timedelta

from dateutil import parser

from src.classifiers.rules import is_entry_level
from src.models import JobPosting
from src.profile import cv_match_points


def _recent_24h(published_at: str, found_at: str) -> bool:
    if not published_at:
        return False
    text = published_at.lower()
    if any(token in text for token in ["hoy", "today", "hora", "hour", "ayer", "yesterday"]):
        return True
    try:
        published = parser.parse(published_at, fuzzy=True)
        found = parser.parse(found_at)
        return found - published <= timedelta(days=1)
    except Exception:
        return False


def score_job(job: JobPosting, profile: dict | None = None) -> None:
    score = 0
    explanation: list[dict[str, int | str]] = []
    text = job.merged_text()

    if job.relevance_classification == "DIRECT_COMEX":
        score += 30
        explanation.append({"points": 30, "reason": "COMEX/importaciones/exportaciones directo"})
    elif job.relevance_classification == "ADJACENT":
        score += 18
        explanation.append({"points": 18, "reason": "Area adyacente: logistica, operaciones o proveedores"})

    if job.experience_classification == "SIN_EXPERIENCIA":
        score += 20
        explanation.append({"points": 20, "reason": "No requiere experiencia"})
    elif job.experience_classification == "EXPERIENCIA_NO_EXCLUYENTE":
        score += 16
        explanation.append({"points": 16, "reason": "Experiencia deseable/no excluyente"})
    elif job.experience_classification == "NO_ESPECIFICA_EXPERIENCIA":
        score += 8
        explanation.append({"points": 8, "reason": "No especifica experiencia obligatoria"})

    if is_entry_level(text):
        score += 15
        explanation.append({"points": 15, "reason": "Pasantia, trainee, junior o intern"})

    if job.travel_minutes is not None:
        if job.travel_minutes <= 30:
            score += 15
            explanation.append({"points": 15, "reason": "Viaje menor a 30 minutos desde Belgrano"})
        elif job.travel_minutes <= 60:
            score += 8
            explanation.append({"points": 8, "reason": "Viaje dentro del máximo de 60 minutos"})

    if _recent_24h(job.published_at, job.found_at):
        score += 10
        explanation.append({"points": 10, "reason": "Publicado en las ultimas 24 horas o muy reciente"})

    if "hibr" in (job.modality or "").lower() or "hybrid" in text.lower():
        score += 5
        explanation.append({"points": 5, "reason": "Modalidad hibrida"})

    if "$" in text or "ars" in text.lower() or "salario" in text.lower() or "sueldo" in text.lower():
        score += 5
        explanation.append({"points": 5, "reason": "Sueldo o rango salarial informado"})

    if profile:
        profile_points, profile_reasons = cv_match_points(text, profile)
        score += profile_points
        explanation.extend(profile_reasons)

    job.score = min(score, 100)
    job.score_explanation = explanation
