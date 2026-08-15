from __future__ import annotations

from datetime import datetime
from pathlib import Path


def write_report(report_dir: str, jobs: list[dict], run: dict, source_summary: list[dict]) -> str:
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = Path(report_dir) / f"radar_comex_{timestamp}.md"

    lines = [
        "# Radar COMEX - Buenos Aires",
        "",
        f"Fecha: {run.get('finished_at', '')}",
        f"Analizados: {run.get('analyzed', 0)}",
        f"Aceptados: {run.get('accepted', 0)}",
        f"Rechazados por experiencia: {run.get('rejected_experience', 0)}",
        f"Rechazados por distancia: {run.get('rejected_distance', 0)}",
        f"Duplicados: {run.get('duplicates', 0)}",
        f"Errores/limitaciones: {run.get('errors', 0)}",
        "",
        "## Mejores oportunidades",
        "",
    ]
    if not jobs:
        lines.append("No hubo avisos aceptados en esta corrida.")
    for idx, job in enumerate(jobs[:30], start=1):
        lines.extend(
            [
                f"### {idx}. {job['title']} - {job.get('company') or 'Sin empresa'}",
                f"- Score: {job.get('score', 0)}/100",
                f"- Ubicacion: {job.get('location') or 'Sin dato'}",
                f"- Viaje estimado desde Belgrano: {_fmt_minutes(job.get('travel_minutes'))}",
                f"- Experiencia: {job.get('experience_classification')}",
                f"- Fuente: {job.get('source')}",
                f"- URL: {job.get('url')}",
                f"- Motivos: {_fmt_reasons(job.get('score_explanation') or [])}",
                "",
            ]
        )

    lines.extend(["## Fuentes", ""])
    for item in source_summary:
        limited = " - limitado por login/CAPTCHA" if item.get("limited") else ""
        lines.append(
            f"- {item['source']}: {item.get('jobs', 0)} candidatos, {item.get('errors', 0)} errores{limited}"
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path.resolve())


def _fmt_minutes(value: float | None) -> str:
    if value is None:
        return "sin dato"
    return f"{int(round(value))} min"


def _fmt_reasons(reasons: list[dict]) -> str:
    return "; ".join(reason.get("reason", "") for reason in reasons[:5]) or "Sin desglose"
