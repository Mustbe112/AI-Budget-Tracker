import { useState } from 'react';

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { baht, fmtVal, labelOf, nice, rowsOf, valueOf } from './normalize.js';
export { baht };

const label = (k) => k.replace(/_/g, ' ');
const isMoney = (k) => /amount|total|spent|budget|remaining|overspen|average|saved|forecast|predicted/i.test(k);
const fmt = (k, v) => /(^|_)id$/i.test(k) ? String(v) : (typeof v === 'number' || (typeof v === 'string' && v !== '' && !isNaN(v) && isMoney(k)))
  ? (isMoney(k) ? baht(v) : String(v)) : String(v ?? '—');

// Renders any JSON response (objects, arrays of objects, scalars) without needing exact schemas.
export function DataView({ data }) {
  if (data == null) return null;
  if (Array.isArray(data)) {
    if (!data.length) return <p className="muted">Nothing to show yet.</p>;
    if (typeof data[0] !== 'object') return <p>{data.join(', ')}</p>;
    const cols = [...new Set(data.flatMap((r) => Object.keys(r)))].filter((c) => typeof data[0][c] !== 'object');
    return (
      <div className="tablewrap"><table>
        <thead><tr>{cols.map((c) => <th key={c}>{label(c)}</th>)}</tr></thead>
        <tbody>{data.map((r, i) => <tr key={i}>{cols.map((c) => <td key={c} className={isMoney(c) ? 'num' : ''}>{fmt(c, r[c])}</td>)}</tr>)}</tbody>
      </table></div>
    );
  }
  if (typeof data === 'object') {
    return (
      <dl className="kv">
        {Object.entries(data).map(([k, v]) => (
          <div key={k} className={typeof v === 'object' && v ? 'kv-block' : 'kv-row'}>
            <dt>{label(k)}</dt>
            <dd>{typeof v === 'object' && v ? <DataView data={v} /> : fmt(k, v)}</dd>
          </div>
        ))}
      </dl>
    );
  }
  return <p>{String(data)}</p>;
}

export const Err = ({ msg }) => (msg ? <p className="err" role="alert">{msg}</p> : null);

export function useAsync() {
  const [state, set] = useState({ loading: false, error: '', data: null });
  const run = async (fn) => {
    set((s) => ({ ...s, loading: true, error: '' }));
    try { const data = await fn(); set({ loading: false, error: '', data }); return data; }
    catch (e) { set({ loading: false, error: e.message, data: null }); }
  };
  return [state, run];
}

export function Field({ f, value, onChange }) {
  const common = { id: f.name, required: f.required, value: value ?? '', onChange: (e) => onChange(f.name, e.target.value) };
  return (
    <label className="field" htmlFor={f.name}>
      <span>{f.label}</span>
      {f.options ? (
        <select {...common}><option value="">Select…</option>{f.options.map((o) => <option key={o}>{o}</option>)}</select>
      ) : (
        <input {...common} type={f.type || 'text'} step={f.type === 'number' ? '0.01' : undefined} min={f.type === 'number' ? '0' : undefined} />
      )}
    </label>
  );
}

export const Stat = ({ label, value, sub, tone }) => (
  <div className={`stat ${tone || ''}`}><span className="stat-l">{label}</span><strong>{value}</strong>{sub && <small>{sub}</small>}</div>
);
export const Empty = ({ children }) => <p className="empty">{children}</p>;
export const Meter = ({ used, total }) => {
  const r = total > 0 ? used / total : 0;
  return <div className="meter" role="img" aria-label={`${Math.round(r * 100)}% used`}><i className={r > 1 ? 'over' : r > 0.8 ? 'warn' : ''} style={{ width: Math.min(r, 1) * 100 + '%' }} /></div>;
};
export const Chart = ({ data, height = 240 }) => (
  <div className="chart" style={{ height }}><ResponsiveContainer><BarChart data={data}>
    <CartesianGrid vertical={false} stroke="#e3eaec" /><XAxis dataKey="name" tickLine={false} fontSize={12} /><YAxis tickLine={false} axisLine={false} fontSize={12} width={48} />
    <Tooltip formatter={(v) => baht(v)} cursor={{ fill: '#eef2f3' }} /><Bar dataKey="value" fill="#0f6b5c" radius={[3, 3, 0, 0]} />
  </BarChart></ResponsiveContainer></div>
);

// Turns any report-like response into stat tiles + chart + table.
export function SmartView({ data }) {
  if (data == null) return null;
  if (data.message && !rowsOf(data).length) return <Empty>{data.message}</Empty>;
  const tiles = [];
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    for (const [k, v] of Object.entries(data)) {
      if (['number', 'string'].includes(typeof v) && v !== '' && k !== 'message' && !/^(note|disclaimer)$/.test(k)) tiles.push([nice(k), fmtVal(k, v)]);
      else if (v && typeof v === 'object' && !Array.isArray(v))
        for (const [k2, v2] of Object.entries(v)) if (['number', 'string'].includes(typeof v2)) tiles.push([`${nice(k)} ${nice(k2)}`, fmtVal(k2, v2)]);
    }
  }
  const rows = rowsOf(data);
  const chart = rows.map((r) => ({ name: labelOf(r), value: valueOf(r) }));
  const cols = rows.length ? Object.keys(rows[0]).filter((c) => typeof rows[0][c] !== 'object') : [];
  const note = data.note || data.disclaimer;
  return (
    <>
      {tiles.length > 0 && <div className="stats">{tiles.slice(0, 8).map(([l, v]) => <Stat key={l} label={l} value={v} />)}</div>}
      {chart.length > 0 && chart.some((c) => c.value) && <section className="panel"><Chart data={chart} /></section>}
      {rows.length > 0 && (
        <section className="panel tablewrap"><table>
          <thead><tr>{cols.map((c) => <th key={c}>{nice(c)}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i}>{cols.map((c) => <td key={c} className={/amount|total|spent|budget|percent/i.test(c) ? 'num' : ''}>{fmtVal(c, r[c])}</td>)}</tr>)}</tbody>
        </table></section>
      )}
      {!tiles.length && !rows.length && <Empty>No data for this period yet.</Empty>}
      {note && <p className="note">{note}</p>}
    </>
  );
}