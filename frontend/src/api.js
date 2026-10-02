// Backend base URL. Set VITE_API_URL in frontend/.env for non-local deployments.
export const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

/** Build an API URL, dropping empty query params. */
export function apiUrl(path, params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.append(k, String(v));
  });
  const query = qs.toString();
  return `${API_BASE}${path}${query ? `?${query}` : ''}`;
}

export async function apiGet(path, params) {
  const res = await fetch(apiUrl(path, params));
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.json();
}
