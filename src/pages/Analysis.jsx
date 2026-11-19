import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Empty, Err, Meter, SmartView, useAsync } from '../components.jsx';
import { baht, num } from '../normalize.js';

const TABS = { overspending: 'Overspending', anomalies: 'Unusual expenses', forecast: 'Forecast', summary: 'Summary' };
const cap = (s) => (s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : '—');
const pct = (v) => `${num(v).toFixed(1)}%`;

/* ---------- Overspending ----------
   Backend shape: { items: [{ budget_id, status: { category, budget_amount, total_spent,
   overspent_amount, utilization_percent, status } }], alerts: [{ message, level }] } */
function Overspending({ data }) {
  const items = Array.isArray(data?.items) ? data.items : [];
  const alerts = Array.isArray(data?.alerts) ? data.alerts : [];
  if (!items.length) return <Empty>No budgets exceeded. You are within your limits.</Empty>;

  return (
    <>
      {alerts.map((a, i) => (
        <div key={i} className="panel" style={{ borderLeft: '4px solid #a11', marginBottom: '.75rem' }}>
          <b className="neg">{a.message}</b>
        </div>
      ))}
      <section className="panel">
        {items.map((it) => {
          const s = it.status || it;           // tolerate flat or nested items
          const spent = num(s.total_spent);
          const budget = num(s.budget_amount);
          const over = num(s.overspent_amount);
          const exceeded = s.status === 'exceeded' || over > 0;
          return (
            <div key={it.budget_id ?? s.category} className="rowbar">
              <div className="rb-top">
                <span>{cap(s.category)} <small className="muted">({s.period}, {s.window_start} to {s.window_end})</small></span>
                {exceeded
                  ? <b className="neg">{baht(over)} over ({pct(s.utilization_percent)})</b>
                  : <b>{baht(num(s.remaining))} left</b>}
              </div>
              <Meter used={spent} total={budget} />
              <small className="muted">{baht(spent)} spent of {baht(budget)}</small>
            </div>
          );
        })}
      </section>
    </>
  );
}

/* ---------- Unusual expenses ----------
   Backend shape: { min_samples, total_anomalies, categories: [{ category, status, sample_count,
   upper_bound, anomalies: [...], message }], note } */
function Anomalies({ data }) {
  const cats = Array.isArray(data?.categories) ? data.categories : [];
  const rows = cats.flatMap((c) => (c.anomalies || []).map((a) => ({ ...a, category: a.category || c.category, upper: c.upper_bound })));
  const lacking = cats.filter((c) => c.status === 'insufficient_data');
  const min = num(data?.min_samples) || 8;

  return (
    <>
      {data?.note && <p className="note">{data.note}</p>}
      {rows.length > 0 ? (
        <section className="panel tablewrap"><table>
          <thead><tr><th>Date</th><th>Category</th><th>Merchant</th><th className="num">Amount</th><th className="num">Usual upper limit</th></tr></thead>
          <tbody>{rows.map((r, i) => (
            <tr key={i}>
              <td>{r.expense_date || r.date || '—'}</td><td>{cap(r.category)}</td><td>{r.merchant || '—'}</td>
              <td className="num neg">{baht(r.amount)}</td><td className="num">{r.upper != null ? baht(r.upper) : '—'}</td>
            </tr>))}</tbody></table></section>
      ) : (
        <Empty>No unusual expenses found.</Empty>
      )}
      {lacking.length > 0 && (
        <section className="panel" style={{ marginTop: '1rem' }}>
          <b>Not enough history yet</b>
          <p className="muted">We need at least {min} expenses in a category to spot unusual spending.</p>
          {lacking.map((c) => (
            <div key={c.category} className="rowbar">
              <div className="rb-top"><span>{cap(c.category)}</span><span>{c.sample_count} / {min} expenses</span></div>
              <Meter used={c.sample_count} total={min} />
            </div>
          ))}
        </section>
      )}
    </>
  );
}

/* ---------- Summary ---------- */
function Card({ label, value }) {
  return <div className="panel" style={{ flex: '1 1 150px' }}><small className="muted">{label}</small><div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{value}</div></div>;
}

function Summary({ data }) {
  const cur = data?.report?.current;
  if (!cur) return <SmartView data={data} />;
  const cats = Array.isArray(cur.by_category) ? cur.by_category : [];
  const budgets = data.report.budgets || data.budgets || [];
  const top = cats[0];

  return (
    <>
      <p className="muted">{cap(data.period)} report: {cur.start} to {cur.end} (as of {data.reference_date})</p>
      <div style={{ display: 'flex', gap: '.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        <Card label="Total spent" value={baht(num(cur.total_spending))} />
        <Card label="Transactions" value={cur.transaction_count} />
        <Card label="Daily average" value={baht(num(cur.average_daily_spending))} />
        <Card label="Top category" value={top ? `${cap(top.category)} (${pct(top.share_percent)})` : '—'} />
      </div>

      <section className="panel">
        <b>Spending by category</b>
        {cats.map((c) => (
          <div key={c.category} className="rowbar">
            <div className="rb-top"><span>{cap(c.category)}</span><span>{baht(num(c.total))} &middot; {pct(c.share_percent)}</span></div>
            <Meter used={num(c.share_percent)} total={100} />
          </div>
        ))}
      </section>

      {Array.isArray(budgets) && budgets.length > 0 && (
        <section className="panel" style={{ marginTop: '1rem' }}>
          <b>Budgets</b>
          {budgets.map((b, i) => {
            const s = b.status || b;
            return (
              <div key={b.budget_id ?? i} className="rowbar">
                <div className="rb-top"><span>{cap(s.category)}</span><span>{baht(num(s.total_spent))} of {baht(num(s.budget_amount))}</span></div>
                <Meter used={num(s.total_spent)} total={num(s.budget_amount)} />
              </div>
            );
          })}
        </section>
      )}
    </>
  );
}

export default function Analysis() {
  const [kind, setKind] = useState('overspending');
  const [win, setWin] = useState('');
  const [{ loading, error, data }, run] = useAsync();
  const params = kind === 'forecast' && win ? { window: win } : undefined;
  useEffect(() => { run(() => api.analysis(kind, params)); /* eslint-disable-next-line */ }, [kind]);

  return (
    <>
      <h1>Analysis</h1>
      <div className="tabs">{Object.entries(TABS).map(([k, l]) => <button key={k} className={k === kind ? 'tab on' : 'tab'} onClick={() => setKind(k)}>{l}</button>)}</div>
      {kind === 'forecast' && (
        <form className="panel grid" onSubmit={(e) => { e.preventDefault(); run(() => api.analysis('forecast', params)); }}>
          <label className="field"><span>Moving-average window (days)</span><input type="number" min="2" max="30" value={win} onChange={(e) => setWin(e.target.value)} placeholder="5" /></label>
          <div className="actions"><button className="btn">Recalculate</button></div>
        </form>
      )}
      {kind === 'forecast' && <p className="note">Forecasts are estimates based on past spending, not guaranteed future expenses.</p>}
      <Err msg={error} />
      {loading ? <p className="muted">Loading…</p>
        : !data ? null
        : kind === 'overspending' ? <Overspending data={data} />
        : kind === 'anomalies' ? <Anomalies data={data} />
        : kind === 'summary' ? <Summary data={data} />
        : <SmartView data={data} />}
      {data != null && <details style={{ marginTop: '1rem' }}><summary className="muted">Raw response from backend</summary><pre style={{ background: '#fff', border: '1px solid var(--line)', padding: '.75rem', overflow: 'auto', fontSize: '.85rem' }}>{JSON.stringify(data, null, 2)}</pre></details>}
    </>
  );
}