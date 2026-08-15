from __future__ import annotations

import argparse
import html
import json
from datetime import datetime
from pathlib import Path

from src.config import load_config
from src.database.sqlite_store import SQLiteStore


CSS = """
:root{--bg:#f5f7f8;--fg:#17202a;--muted:#60717f;--line:#d7e0e7;--panel:#fff;--accent:#0f5b7f;--dark:#123348;--ok:#2c7a5c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:Arial,Helvetica,sans-serif}
.page{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:28px 0 42px}.summary{display:grid;grid-template-columns:minmax(0,1fr) 420px;gap:24px;align-items:end;margin-bottom:20px}
.eyebrow,.source{margin:0 0 8px;color:var(--ok);font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:0}h1,h2,p,dl,dd{margin:0}
h1{max-width:780px;font-size:40px;line-height:1.08}.lead{max-width:780px;margin-top:12px;color:var(--muted);font-size:17px;line-height:1.5}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.stats div,.job{background:var(--panel);border:1px solid var(--line);border-radius:8px}
.stats div{min-height:82px;padding:12px}.stats dt{color:var(--muted);font-size:13px}.stats dd{margin-top:7px;font-size:20px;font-weight:850}
.jobs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.job{display:flex;flex-direction:column;min-height:360px;padding:16px}
.jobTop{display:grid;grid-template-columns:minmax(0,1fr) 52px;gap:14px}h2{font-size:20px;line-height:1.22}.company{margin-top:7px;color:var(--muted);line-height:1.35}
.score{width:52px;height:48px;display:grid;place-items:center;border-radius:8px;background:var(--dark);color:#fff;font-size:20px}.chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 12px}
.chips span{border:1px solid #cdd8df;border-radius:999px;padding:6px 9px;color:#2d3a44;background:#f7fafb;font-size:12px}.description{color:#3c4b57;line-height:1.48;max-height:96px;overflow:hidden}
.reasons{margin:14px 0 18px;padding-left:18px;color:var(--muted);font-size:14px;line-height:1.4}.apply{margin-top:auto;min-height:44px;display:inline-flex;align-items:center;justify-content:center;gap:8px;border-radius:8px;background:var(--accent);color:#fff;font-weight:850;text-decoration:none}
.empty{background:#fff;border:1px solid var(--line);border-radius:8px;padding:22px;color:var(--muted)}@media(max-width:880px){.summary,.jobs{grid-template-columns:1fr}.stats{grid-template-columns:1fr}h1{font-size:32px}}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    config = load_config()
    store = SQLiteStore(config["app"]["database_path"])
    try:
        jobs = [
            _public_job(job)
            for job in store.list_jobs(include_rejected=False)
            if _is_direct_application_url(job.get("url", ""))
        ]
        latest = _public_run(store.latest_run())
    finally:
        store.close()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reference_location": config["app"]["reference_location"],
        "max_travel_minutes": config["app"]["max_travel_minutes"],
        "latest_run": latest,
        "jobs": jobs,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    (output_dir / "jobs.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "index.html").write_text(_render_html(payload), encoding="utf-8")
    print(f"Exported static site with {len(jobs)} jobs to {output_dir}")
    return 0


def _public_job(job: dict) -> dict:
    return {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "source": job.get("source", ""),
        "url": job.get("url", ""),
        "score": job.get("score", 0),
        "travel_minutes": job.get("travel_minutes"),
        "distance_km": job.get("distance_km"),
        "experience": job.get("experience_classification", ""),
        "relevance": job.get("relevance_classification", ""),
        "description": job.get("description", ""),
        "reasons": [item.get("reason", "") for item in job.get("score_explanation", [])],
    }


def _render_html(payload: dict) -> str:
    jobs = sorted(payload["jobs"], key=lambda item: item.get("score", 0), reverse=True)
    cards = "\n".join(_render_job(job) for job in jobs) or '<div class="empty">No hay ofertas disponibles.</div>'
    generated = _format_date(payload.get("generated_at", ""))
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Radar COMEX Buenos Aires</title>
  <meta name="description" content="Ofertas de comercio exterior cerca de Belgrano con links de postulacion.">
  <style>{CSS}</style>
</head>
<body>
  <main class="page">
    <section class="summary">
      <div>
        <p class="eyebrow">Radar publico de empleos</p>
        <h1>Ofertas COMEX cerca de Belgrano</h1>
        <p class="lead">Avisos filtrados para comercio exterior, importaciones, exportaciones, aduana y logistica internacional, priorizando pasantias, trainee y junior sin experiencia excluyente.</p>
      </div>
      <dl class="stats" aria-label="Resumen de resultados">
        <div><dt>Ofertas</dt><dd>{len(jobs)}</dd></div>
        <div><dt>Maximo viaje</dt><dd>{payload.get("max_travel_minutes", 60)} min</dd></div>
        <div><dt>Actualizado</dt><dd>{html.escape(generated)}</dd></div>
      </dl>
    </section>
    <section class="jobs" aria-label="Ofertas encontradas">{cards}</section>
  </main>
</body>
</html>
"""


def _render_job(job: dict) -> str:
    reasons = "".join(f"<li>{html.escape(reason)}</li>" for reason in job.get("reasons", [])[:3])
    return f"""<article class="job">
  <div class="jobTop">
    <div>
      <p class="source">{html.escape(job.get("source", ""))}</p>
      <h2>{html.escape(job.get("title", ""))}</h2>
      <p class="company">{html.escape(job.get("company", ""))} - {html.escape(job.get("location", ""))}</p>
    </div>
    <strong class="score">{int(job.get("score") or 0)}</strong>
  </div>
  <div class="chips">
    <span>{html.escape(job.get("experience", ""))}</span>
    <span>{html.escape(job.get("relevance", ""))}</span>
    <span>{_minutes(job.get("travel_minutes"))} desde Belgrano</span>
  </div>
  <p class="description">{html.escape(job.get("description", ""))}</p>
  <ul class="reasons">{reasons}</ul>
  <a class="apply" href="{html.escape(job.get("url", ""), quote=True)}" target="_blank" rel="noreferrer">Postularme en el aviso <span>Abrir</span></a>
</article>"""


def _minutes(value: float | None) -> str:
    if value is None:
        return "Sin dato"
    return f"{round(value)} min"


def _format_date(value: str) -> str:
    if not value:
        return "Actualizado"
    return value.replace("T", " ")[:16]


def _is_direct_application_url(url: str) -> bool:
    lowered = (url or "").lower()
    if not lowered.startswith("http"):
        return False
    return "/jobs/search" not in lowered and "keywords=" not in lowered


def _public_run(run: dict | None) -> dict | None:
    if not run:
        return None
    return {
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "analyzed": run.get("analyzed", 0),
        "accepted": run.get("accepted", 0),
        "rejected_experience": run.get("rejected_experience", 0),
        "rejected_distance": run.get("rejected_distance", 0),
        "duplicates": run.get("duplicates", 0),
        "errors": run.get("errors", 0),
    }


if __name__ == "__main__":
    raise SystemExit(main())
