import React, { useEffect, useMemo, useState } from "react";
import { ExternalLink, Filter, MapPin, RefreshCw, Search, SlidersHorizontal } from "lucide-react";
import { createRoot } from "react-dom/client";
import { fetchJobs, fetchStats } from "./lib/api";
import "./styles.css";

function App() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState(null);
  const [minScore, setMinScore] = useState(55);
  const [query, setQuery] = useState("");
  const [includeRejected, setIncludeRejected] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const [nextJobs, nextStats] = await Promise.all([
      fetchJobs({ includeRejected, minScore, q: query }),
      fetchStats(),
    ]);
    setJobs(nextJobs);
    setStats(nextStats);
    setLoading(false);
  }

  useEffect(() => {
    load().catch(() => setLoading(false));
  }, [minScore, includeRejected]);

  const sources = useMemo(() => [...new Set(jobs.map((job) => job.source).filter(Boolean))], [jobs]);

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>Radar COMEX</h1>
          <p>Belgrano a Buenos Aires, entrada laboral y pasantias</p>
        </div>
        <button className="iconButton" onClick={load} title="Actualizar">
          <RefreshCw size={18} />
        </button>
      </header>

      <section className="metrics">
        <Metric label="Aceptados" value={stats?.accepted ?? 0} />
        <Metric label="Total DB" value={stats?.total ?? 0} />
        <Metric label="Top score" value={stats?.top_score ?? 0} />
        <Metric label="Ultima corrida" value={stats?.latest_run?.finished_at?.slice(0, 16) ?? "-"} />
      </section>

      <section className="filters">
        <label className="searchBox">
          <Search size={17} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && load()}
            placeholder="Buscar titulo, empresa, fuente"
          />
        </label>
        <label className="range">
          <SlidersHorizontal size={17} />
          <span>{minScore}</span>
          <input
            type="range"
            min="0"
            max="100"
            value={minScore}
            onChange={(event) => setMinScore(Number(event.target.value))}
          />
        </label>
        <label className="toggle">
          <input
            type="checkbox"
            checked={includeRejected}
            onChange={(event) => setIncludeRejected(event.target.checked)}
          />
          <Filter size={17} />
          Rechazados
        </label>
      </section>

      <section className="workspace">
        <JobList jobs={jobs} loading={loading} />
        <MapPanel jobs={jobs} sources={sources} />
      </section>
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function JobList({ jobs, loading }) {
  if (loading) return <div className="empty">Cargando avisos...</div>;
  if (!jobs.length) return <div className="empty">No hay avisos con estos filtros.</div>;
  return (
    <div className="list">
      {jobs.map((job) => (
        <article className={`job ${job.status?.toLowerCase()}`} key={job.id}>
          <div className="jobHead">
            <div>
              <h2>{job.title}</h2>
              <p>{job.company || "Sin empresa"} · {job.location || "Sin ubicacion"}</p>
            </div>
            <div className="score">{job.score}</div>
          </div>
          <div className="chips">
            <span>{job.experience_classification}</span>
            <span>{job.relevance_classification}</span>
            <span>{job.travel_minutes ? `${Math.round(job.travel_minutes)} min` : "Sin ruta"}</span>
          </div>
          <p className="description">{job.description || "Sin descripcion publica suficiente."}</p>
          <div className="actions">
            <span>{job.source}</span>
            <a href={job.url} target="_blank" rel="noreferrer">
              Abrir <ExternalLink size={15} />
            </a>
          </div>
        </article>
      ))}
    </div>
  );
}

function MapPanel({ jobs, sources }) {
  const points = jobs.filter((job) => job.latitude && job.longitude);
  return (
    <aside className="mapPanel">
      <div className="mapTitle">
        <MapPin size={18} />
        Ubicaciones estimadas
      </div>
      <div className="mapCanvas">
        <div className="belgrano">Belgrano</div>
        {points.map((job) => (
          <a
            key={job.id}
            className="pin"
            href={job.url}
            target="_blank"
            rel="noreferrer"
            title={`${job.title} - ${job.company || ""}`}
            style={pinStyle(job)}
          />
        ))}
      </div>
      <div className="legend">
        {sources.slice(0, 6).map((source) => (
          <span key={source}>{source}</span>
        ))}
      </div>
    </aside>
  );
}

function pinStyle(job) {
  const lat = Number(job.latitude);
  const lng = Number(job.longitude);
  const x = Math.max(5, Math.min(92, 50 + (lng + 58.4583) * 380));
  const y = Math.max(6, Math.min(92, 48 - (lat + 34.5627) * 300));
  return { left: `${x}%`, top: `${y}%` };
}

createRoot(document.getElementById("root")).render(<App />);
