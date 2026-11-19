import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api, fetchAll, token } from '../api.js';
import { Empty, Err, Meter, Stat } from '../components.jsx';
import { addDays, bAmount, bPeriod, baht, budgetWindow, monthOf, num, pick, rowsOf, sumBaht, today } from '../normalize.js';

const asList = (d) => (Array.isArray(d) ? d : d?.items || []);

export default function Dashboard({ go }) {
  const [x, setX] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [exp, inc, bud] = await Promise.all([fetchAll('/expenses'), fetchAll('/income'), api.list('/budgets')]);
        const [fc, an] = await Promise.allSettled([api.analysis('forecast'), api.analysis('anomalies')]);
        setX({ exp: asList(exp), inc: asList(inc), bud: asList(bud), fc: fc.value, an: an.value });
      } catch (e) { setError(e.message); }
    })();
  }, []);

  const m = useMemo(() => {
    if (!x) return null;
    const now = today(), mo = monthOf(now);
    const expM = x.exp.filter((e) => monthOf(e.expense_date || '') === mo);
    const incM = x.inc.filter((i) => monthOf(i.income_date || '') === mo);
    const spent = sumBaht(expM), income = sumBaht(incM);
    // spending per category this month, biggest first
    const cat = {};
    expM.forEach((e) => { cat[e.category] = (cat[e.category] || 0) + Math.round(num(e.amount) * 100); });
    const cats = Object.entries(cat).map(([name, c]) => ({ name, value: c / 100 })).sort((a, b) => b.value - a.value);
    // last 14 days
    const days = Array.from({ length: 14 }, (_, i) => addDays(now, i - 13)).map((d) => ({ name: d.slice(8), value: sumBaht(x.exp.filter((e) => e.expense_date === d)) }));
    // each budget: spend in its category inside its window
    const budgets = x.bud.map((b) => {
      const [from, to] = budgetWindow(b, now);
      const used = sumBaht(x.exp.filter((e) => e.category === b.category && e.expense_date >= from && e.expense_date <= to));
      return { ...b, used, limit: bAmount(b) };
    }).sort((a, b) => b.used / (b.limit || 1) - a.used / (a.limit || 1));
    const totalLimit = budgets.reduce((a, b) => a + b.limit, 0), totalUsed = budgets.reduce((a, b) => a + b.used, 0);
    const recent = [...x.exp].sort((a, b) => (b.expense_date || '').localeCompare(a.expense_date || '')).slice(0, 6);
    return { spent, income, balance: income - spent, cats, days, budgets, totalLimit, totalUsed, recent, over: budgets.filter((b) => b.used > b.limit) };
  }, [x]);

  if (error) return <><h1>Overview</h1><Err msg={error} /></>;
  if (!m) return <><h1>Overview</h1><p className="muted">Loading your dashboard…</p></>;

  const fcVal = x.fc?.forecast?.forecast_next_day ?? null;
  const anomalyCount = num(x.an?.total_anomalies);
  const first = !x.exp.length && !x.inc.length && !x.bud.length;
  const monthName = new Date().toLocaleString('en-US', { month: 'long', year: 'numeric' });

  return (
    <>
      <div className="bar"><div><h1 style={{ marginBottom: 0 }}>Hello{token.user() ? `, ${token.user()}` : ''}</h1><p className="muted" style={{ margin: 0 }}>{monthName}</p></div>
        <div className="actions"><button className="btn" onClick={() => go('expenses')}>Add expense</button><button className="btn ghost" onClick={() => go('receipts')}>Scan receipt</button></div></div>

      {first && <p className="note">Welcome. Add an expense, an income and a budget to fill in this dashboard.</p>}

      {m.over.length > 0 && (
        <div className="alert" role="status"><strong>{m.over.length} budget{m.over.length > 1 ? 's' : ''} exceeded</strong>
          {m.over.map((b) => <span key={b.id} className="chip">{b.category} ({bPeriod(b)}): {baht(b.used - b.limit)} over</span>)}</div>
      )}

      <div className="stats">
        <Stat label="Income this month" value={baht(m.income)} />
        <Stat label="Spent this month" value={baht(m.spent)} />
        <Stat label="Balance" value={baht(m.balance)} tone={m.balance < 0 ? 'neg' : 'pos'} />
        <Stat label="Budget used" value={m.totalLimit ? Math.round((m.totalUsed / m.totalLimit) * 100) + '%' : '—'} sub={m.totalLimit ? `${baht(m.totalUsed)} of ${baht(m.totalLimit)}` : 'No budgets yet'} tone={m.totalUsed > m.totalLimit && m.totalLimit ? 'neg' : ''} />
      </div>

      <div className="cols">
        <section className="panel">
          <h2>Spending, last 14 days</h2>
          <div className="chart"><ResponsiveContainer><BarChart data={m.days}><CartesianGrid vertical={false} stroke="#ded8d1" /><XAxis dataKey="name" tickLine={false} fontSize={12} /><YAxis tickLine={false} axisLine={false} fontSize={12} width={44} /><Tooltip formatter={(v) => baht(v)} labelFormatter={(l) => `Day ${l}`} cursor={{ fill: '#eee7de' }} /><Bar dataKey="value" fill="#bd7b3d" radius={[2, 2, 0, 0]} /></BarChart></ResponsiveContainer></div>
        </section>
        <section className="panel">
          <h2>By category</h2>
          {m.cats.length ? m.cats.map((c) => (
            <div key={c.name} className="rowbar"><div className="rb-top"><span>{c.name}</span><b>{baht(c.value)}</b></div><Meter used={c.value} total={m.cats[0].value} /></div>
          )) : <Empty>No spending this month.</Empty>}
        </section>
      </div>

      <div className="cols">
        <section className="panel">
          <div className="bar"><h2>Budgets</h2><button className="link" onClick={() => go('budgets')}>Manage</button></div>
          {m.budgets.length ? m.budgets.slice(0, 6).map((b) => (
            <div key={b.id} className="rowbar"><div className="rb-top"><span>{b.category} <small className="muted">{bPeriod(b)}</small></span>
              <b className={b.used > b.limit ? 'neg' : ''}>{b.used > b.limit ? `${baht(b.used - b.limit)} over` : `${baht(b.limit - b.used)} left`}</b></div>
              <Meter used={b.used} total={b.limit} /><small className="muted">{baht(b.used)} of {baht(b.limit)}</small></div>
          )) : <Empty>No budgets yet. Create one to track your limits.</Empty>}
        </section>
        <section className="panel">
          <div className="bar"><h2>Recent expenses</h2><button className="link" onClick={() => go('expenses')}>View all</button></div>
          {m.recent.length ? <ul className="list">{m.recent.map((e) => <li key={e.id}><div><b>{e.merchant || e.category}</b><small className="muted">{e.category} · {e.expense_date}</small></div><span>{baht(e.amount)}</span></li>)}</ul> : <Empty>No expenses yet.</Empty>}
        </section>
      </div>

      {(fcVal != null || anomalyCount > 0) && (
        <div className="cols">
          {fcVal != null && <section className="panel"><h2>Forecast</h2><p className="big">{baht(fcVal)}</p><p className="muted">Estimated spending for the next day, based on recent days. It is an estimate, not a guarantee.</p></section>}
          {anomalyCount > 0 && <section className="panel"><h2>Unusual expenses</h2><p className="big">{anomalyCount}</p><p className="muted">flagged for review. Nothing is changed automatically.</p><button className="link left" onClick={() => go('analysis')}>Review them</button></section>}
        </div>
      )}
    </>
  );
}
