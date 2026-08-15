from __future__ import annotations

from src.classifiers.rules import normalize


def cv_match_points(text: str, profile: dict) -> tuple[int, list[dict[str, int | str]]]:
    clean = normalize(text)
    explanations: list[dict[str, int | str]] = []
    points = 0

    buckets = [
        ("target_roles", 8, "Coincide con el objetivo laboral del CV"),
        ("education", 5, "Aprovecha formacion en RRII/comercio internacional"),
        ("strengths", 4, "Alinea con habilidades del CV"),
    ]
    for key, weight, reason in buckets:
        matches = [item for item in profile.get(key, []) if normalize(item) in clean]
        if matches:
            points += weight
            explanations.append({"points": weight, "reason": f"{reason}: {', '.join(matches[:3])}"})

    if "ingles" in clean or "english" in clean:
        points += 3
        explanations.append({"points": 3, "reason": "Requiere o valora ingles, fortaleza del CV"})

    return min(points, 15), explanations
