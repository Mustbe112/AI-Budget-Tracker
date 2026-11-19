import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Chart, Empty, Err, Meter, Stat, useAsync } from '../components.jsx';
import { baht, num } from '../normalize.js';

const KINDS = ['daily', 'weekly', 'monthly', 'categories', 'comparison'];
const cap = (s) => (s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : '—');
const share = (v) => `${num(v).toFixed(1)}%`;
const signed = (v) => `${num(v) > 0 ? '+' : ''}${num(v).toFixed(1)}%`;

function CategoryBars({ cats, title = 'By category' }) {
  if (!cats?.length) return <Empty>No spending in this period.</Empty>;
  return (
    <section className="panel"><h2>{title}</h2>
      {cats.map((c) => (
        <div key={c.category} className="rowbar">
          <div className="rb-top"><span>{cap(c.category)}</span><b>{baht(c.total)} <small className="muted">{share(c.share_percent)}</small></b></div>
          <Meter used={num(c.share_percent)} total={100} />
        </div>
      ))}
    </section>
  );
}

// GET /reports/daily|weekly|monthly -> { summary: {...}, income_total, net }
function Spending({ d }) {
  const s = d.summary || {};
  return (
    <>
      <p className="muted">{cap(d.period)} report, {s.start} to {s.end}</p>
      <div className="stats">
        <Stat label="Spent" value={baht(s.total_spending)} />
        <Stat label="Income" value={baht(d.income_total)} />
        <Stat label="Net" value={baht(d.net)} tone={num(d.net) < 0 ? 'neg' : 'pos'} />
        <Stat label="Transactions" value={s.transaction_count ?? 0} />
        <Stat label="Daily average" value={baht(s.average_daily_spending)} />
        {s.budget_amount != null && <Stat label="Budget used" value={share(s.budget_utilization_percent)} sub={`of ${baht(s.budget_amount)}`} />}
      </div>
      <CategoryBars cats={s.by_category} />
    </>
  );
}

// GET /reports/categories -> { total_spending, categories: [{category,total,share_percent}] }
function Categories({ d }) {
  const cats = d.categories || [];
  return (
    <>
      <p className="muted">{d.start_date} to {d.end_date}</p>
      <div className="stats"><Stat label="Total spent" value={baht(d.total_spending)} /></div>
      {cats.length > 0 && <section className="panel"><Chart data={cats.map((c) => ({ name: cap(c.category), value: num(c.total) }))} /></section>}
      <CategoryBars cats={cats} title="Breakdown" />
    </>
  );
}

// GET /reports/comparison -> { current, previous, comparison: { previous_total, current_total, change_amount, change_percent, trend, categories[] } }
function Comparison({ d }) {
  const c = d.comparison || {};
  const up = num(c.change_amount) > 0;
  return (
    <>
      <p className="muted">This {d.period?.replace('ly', '')} ({d.current?.start} to {d.current?.end}) vs the one before ({d.previous?.start} to {d.previous?.end})</p>
      <div className="stats">
        <Stat label="Previous" value={baht(c.previous_total)} />
        <Stat label="Current" value={baht(c.current_total)} />
        <Stat label="Change" value={`${up ? '+' : ''}${baht(c.change_amount)}`} sub={c.change_percent != null ? signed(c.change_percent) : 'No previous spending'} tone={up ? 'neg' : 'pos'} />
      </div>
      {c.categories?.length > 0 ? (
        <section className="panel tablewrap"><table>
          <thead><tr><th>Category</th><th className="num">Previous</th><th className="num">Current</th><th className="num">Change</th><th>Trend</th></tr></thead>
          <tbody>{c.categories.map((r) => (
            <tr key={r.category}><td>{cap(r.category)}</td><td className="num">{baht(r.previous)}</td><td className="num">{baht(r.current)}</td>
              <td className={`num ${num(r.change_amount) > 0 ? 'neg' : ''}`}>{r.change_percent != null ? signed(r.change_percent) : '—'}</td><td>{cap(r.trend)}</td></tr>
          ))}</tbody></table></section>
      ) : <Empty>No category data to compare.</Empty>}
    </>
  );
}

export default function Reports() {
  const [kind, setKind] = useState('daily');
  const [p, setP] = useState({ date: '', start_date: '', end_date: '', period: 'weekly' });
  const [{ loading, error, data }, run] = useAsync();
  const load = () => run(() => api.report(kind, kind === 'categories' ? { start_date: p.start_date, end_date: p.end_date } : kind === 'comparison' ? { date: p.date, period: p.period } : { date: p.date }));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [kind]);
  const set = (k) => (e) => setP({ ...p, [k]: e.target.value });

  return (
    <>
      <h1>Reports</h1>
      <div className="tabs">{KINDS.map((k) => <button key={k} className={k === kind ? 'tab on' : 'tab'} onClick={() => setKind(k)}>{k}</button>)}</div>
      <form className="panel grid" onSubmit={(e) => { e.preventDefault(); load(); }}>
        {kind === 'categories' ? (<>
          <label className="field"><span>Start date</span><input type="date" value={p.start_date} onChange={set('start_date')} /></label>
          <label className="field"><span>End date</span><input type="date" value={p.end_date} onChange={set('end_date')} /></label>
        </>) : (
          <label className="field"><span>Any date in the period</span><input type="date" value={p.date} onChange={set('date')} /></label>
        )}
        {kind === 'comparison' && <label className="field"><span>Compare</span><select value={p.period} onChange={set('period')}><option value="daily">Day vs previous day</option><option value="weekly">Week vs previous week</option><option value="monthly">Month vs previous month</option></select></label>}
        <div className="actions"><button className="btn">Update report</button></div>
      </form>
      <Err msg={error} />
      {loading ? <p className="muted">Loading…</p> : !data ? null
        : kind === 'categories' ? <Categories d={data} /> : kind === 'comparison' ? <Comparison d={data} /> : <Spending d={data} />}
    </>
  );
}