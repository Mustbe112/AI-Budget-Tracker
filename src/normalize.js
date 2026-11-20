// Helpers that make the UI tolerant of small differences in backend response shapes.
export const num = (v) => { const n = Number(v); return Number.isFinite(n) ? n : 0; };
export const pick = (o, keys) => { for (const k of keys) if (o && o[k] != null) return o[k]; return undefined; };
export const nice = (k) => k.replace(/_/g, ' ');
export const baht = (n) => '฿' + num(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const pct = (n) => `${num(n) > 0 ? '+' : ''}${num(n).toFixed(1)}%`;

export const rowsOf = (d) => {
  if (Array.isArray(d)) return d;
  if (d && typeof d === 'object') for (const v of Object.values(d)) if (Array.isArray(v) && v.length && typeof v[0] === 'object') return v;
  return [];
};
export const labelOf = (r) => String(pick(r, ['category', 'label', 'date', 'period', 'name', 'week', 'month']) ?? '');
export const valueOf = (r) => num(pick(r, ['total', 'amount', 'spent', 'total_spent', 'total_spending', 'value', 'sum']));

const isPct = (k) => /percent|change|utilization|%/i.test(k);
const isMoney = (k) => /amount|total|spent|budget|remaining|over|average|saved|forecast|predict|estimate|income|expense|bound|spending/i.test(k);
export const fmtVal = (k, v) => {
  if (v == null || v === '') return '—';
  if (isNaN(Number(v))) return String(v);
  if (isPct(k)) return pct(v);
  return isMoney(k) ? baht(v) : String(v);
};

// Month helpers (dates are ISO strings: YYYY-MM-DD)
export const today = () => new Date().toISOString().slice(0, 10);
export const monthOf = (iso) => iso.slice(0, 7);
export const addDays = (iso, n) => { const d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };

// Budget field names differ between backends; accept either spelling.
export const bAmount = (b) => num(pick(b, ['amount', 'budget_amount']));
export const bPeriod = (b) => pick(b, ['period', 'budget_period']);

// Window a budget applies to. Uses its own dates if set, otherwise the current day/week/month.
export function budgetWindow(b, now = today()) {
  if (b.start_date && b.end_date) return [b.start_date, b.end_date];
  if (bPeriod(b) === 'daily') return [now, now];
  if (bPeriod(b) === 'weekly') {
    const dow = (new Date(now + 'T00:00:00Z').getUTCDay() + 6) % 7; // Monday = 0
    return [addDays(now, -dow), addDays(now, 6 - dow)];
  }
  return [now.slice(0, 7) + '-01', now.slice(0, 7) + '-31'];
}
// Sum in satang (integers) so display totals don't drift.
export const sumBaht = (rows, f = 'amount') => rows.reduce((a, r) => a + Math.round(num(r[f]) * 100), 0) / 100;
