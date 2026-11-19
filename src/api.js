// All backend calls live here. Base URL: /api (proxied to FastAPI in dev).
const BASE = import.meta.env.VITE_API_URL || '/api';

export const token = {
  user: () => localStorage.getItem('abt_user') || '',
  setUser: (u) => localStorage.setItem('abt_user', u),
  get: () => localStorage.getItem('abt_token'),
  set: (t) => localStorage.setItem('abt_token', t),
  clear: () => { localStorage.removeItem('abt_token'); localStorage.removeItem('abt_user'); },
};

async function req(path, { method = 'GET', body, form, params } = {}) {
  const clean = Object.entries(params || {}).filter(([, v]) => v !== '' && v != null);
  const qs = clean.length ? '?' + new URLSearchParams(clean) : '';
  const headers = {};
  if (token.get()) headers.Authorization = `Bearer ${token.get()}`;
  let payload;
  if (form) payload = form; // FormData or URLSearchParams
  else if (body) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body); }

  const res = await fetch(BASE + path + qs, { method, headers, body: payload });
  if (res.status === 401) { token.clear(); window.dispatchEvent(new Event('abt-logout')); }
  if (!res.ok) {
    let detail;
    try { detail = (await res.json()).detail; } catch { /* no body */ }
    throw new Error(
      typeof detail === 'string' ? detail
        : Array.isArray(detail) ? detail.map((e) => e.msg).join(', ')
        : `Request failed (${res.status})`
    );
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  // Auth (assumed routes — confirm with backend owner)
  register: (b) => req('/auth/register', { method: 'POST', body: b }),
  login: (username, password) =>
    req('/auth/login', { method: 'POST', form: new URLSearchParams({ username, password }) }),

  // Generic CRUD for /expenses, /income, /budgets
  list: (path, params) => req(path, { params }),
  create: (path, b) => req(path, { method: 'POST', body: b }),
  update: (path, id, b) => req(`${path}/${id}`, { method: 'PUT', body: b }),
  remove: (path, id) => req(`${path}/${id}`, { method: 'DELETE' }),

  budgetCheck: () => req('/budgets/check'),
  report: (kind, params) => req(`/reports/${kind}`, { params }), // daily|weekly|monthly|categories|comparison
  analysis: (kind, params) => req(`/analysis/${kind}`, { params }), // overspending|anomalies|forecast|summary

  receiptUpload: (file) => { const f = new FormData(); f.append('file', file); return req('/receipts/upload', { method: 'POST', form: f }); },
  receiptExtract: (b) => req('/receipts/extract', { method: 'POST', body: b }),
  receiptConfirm: (b) => req('/receipts/confirm', { method: 'POST', body: b }),

  // Profile (assumed routes — confirm with backend owner)
  me: () => req('/auth/me'),
  updateMe: (b) => req('/auth/me', { method: 'PUT', body: b }),
  changePassword: (b) => req('/auth/me/password', { method: 'PUT', body: b }),

  aiRecommend: (b = {}) => req('/ai/recommendations', { method: 'POST', body: b }),
  aiChat: (question) => req('/ai/chat', { method: 'POST', body: { question } }),
};

// Backends usually cap page size (yours: limit <= 100), so fetch every page.
// Sends both skip and offset since the paging parameter name isn't known; stops when a page adds nothing new.
export async function fetchAll(path, pageSize = 100, maxPages = 20) {
  const seen = new Map();
  for (let i = 0; i < maxPages; i++) {
    const data = await api.list(path, { limit: pageSize, skip: i * pageSize, offset: i * pageSize });
    const rows = Array.isArray(data) ? data : data?.items || [];
    const before = seen.size;
    rows.forEach((r, j) => seen.set(r.id ?? `${i}-${j}`, r));
    if (rows.length < pageSize || seen.size === before) break;
  }
  return [...seen.values()];
}