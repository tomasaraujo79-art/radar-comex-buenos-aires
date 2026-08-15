const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function fetchJobs({ includeRejected, minScore, q }) {
  const params = new URLSearchParams({
    include_rejected: String(includeRejected),
    min_score: String(minScore),
    q,
  });
  const response = await fetch(`${API_BASE}/api/jobs?${params}`);
  if (!response.ok) throw new Error("No se pudieron cargar los avisos");
  return response.json();
}

export async function fetchStats() {
  const response = await fetch(`${API_BASE}/api/stats`);
  if (!response.ok) throw new Error("No se pudieron cargar las metricas");
  return response.json();
}
