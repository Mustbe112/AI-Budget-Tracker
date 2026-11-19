import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';
import { Empty, Err, Field, Meter, baht } from '../components.jsx';
import { num } from '../normalize.js';

// Budget status from GET /budgets/check:
// { items: [{ budget_id, status: { category, period, budget_amount, total_spent, overspent_amount, remaining, status } }], alerts: [{ level, message }] }
const cap = (t) => (t ? String(t).charAt(0).toUpperCase() + String(t).slice(1) : '');
function BudgetStatus({ data }) {
  const items = Array.isArray(data?.items) ? data.items : [];
  const alerts = Array.isArray(data?.alerts) ? data.alerts : [];
  if (!items.length) return <Empty>No budgets to check yet.</Empty>;
  return (
    <>
      {alerts.map((a, i) => <div key={i} className="alert" role="status"><strong>{a.message}</strong></div>)}
      {items.map((it, i) => {
        const s = it.status || it;
        const spent = num(s.total_spent), limit = num(s.budget_amount), over = num(s.overspent_amount);
        const exceeded = s.status === 'exceeded' || over > 0;
        const left = s.remaining != null ? num(s.remaining) : limit - spent;
        return (
          <div key={it.budget_id ?? i} className="rowbar">
            <div className="rb-top"><span>{cap(s.category)} <small className="muted">{s.period}</small></span>
              <b className={exceeded ? 'neg' : ''}>{exceeded ? `${baht(over || spent - limit)} over` : `${baht(left)} left`}</b></div>
            <Meter used={spent} total={limit} />
            <small className="muted">{baht(spent)} of {baht(limit)}</small>
          </div>
        );
      })}
    </>
  );
}

// One reusable page for expenses, income and budgets (list + create + edit + delete).
export default function Resource({ title, path, fields, cols, filters = [], showCheck }) {
  const [rows, setRows] = useState([]);
  const [check, setCheck] = useState(null);
  const [form, setForm] = useState({});
  const [editing, setEditing] = useState(null);
  const [filter, setFilter] = useState({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const data = await api.list(path, filter);
      setRows(Array.isArray(data) ? data : data.items || []);
      if (showCheck) setCheck(await api.budgetCheck());
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }, [path, filter, showCheck]);
  useEffect(() => { load(); }, [load]);

  const onChange = (k, v) => setForm((s) => ({ ...s, [k]: v }));
  const reset = () => { setForm({}); setEditing(null); };

  const save = async (e) => {
    e.preventDefault(); setError('');
    const body = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ''));
    try {
      editing ? await api.update(path, editing, body) : await api.create(path, body);
      reset(); load();
    } catch (err) { setError(err.message); }
  };
  const del = async (id) => {
    if (!confirm('Delete this record? This cannot be undone.')) return;
    try { await api.remove(path, id); load(); } catch (err) { setError(err.message); }
  };
  const edit = (r) => {
    setEditing(r.id);
    setForm(Object.fromEntries(fields.map((f) => [f.name, r[f.name] ?? ''])));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      <h1>{title}</h1>
      {showCheck && check && <section className="panel"><h2>Budget status</h2><BudgetStatus data={check} /></section>}
      <form className="panel grid" onSubmit={save}>
        <h2 className="span">{editing ? `Edit ${title.toLowerCase()} record` : `Add to ${title.toLowerCase()}`}</h2>
        {fields.map((f) => <Field key={f.name} f={f} value={form[f.name]} onChange={onChange} />)}
        <div className="actions span">
          <button className="btn">{editing ? 'Save changes' : 'Add'}</button>
          {editing && <button type="button" className="btn ghost" onClick={reset}>Cancel</button>}
        </div>
      </form>
      <Err msg={error} />
      <section className="panel">
        <div className="bar">
          <h2>History</h2>
          {filters.map((k) => (
            <input key={k} className="mini" placeholder={`Filter by ${k}`} value={filter[k] || ''} onChange={(e) => setFilter({ ...filter, [k]: e.target.value })} />
          ))}
        </div>
        {loading ? <p className="muted">Loading…</p> : !rows.length ? <p className="muted">No records yet. Use the form above to add your first one.</p> : (
          <div className="tablewrap"><table>
            <thead><tr>{cols.map((c) => <th key={c}>{c.replace(/_/g, ' ')}</th>)}<th /></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.id}>
                {cols.map((c) => <td key={c} className={c.includes('amount') ? 'num' : ''}>{c.includes('amount') ? baht(r[c]) : r[c] ?? '—'}</td>)}
                <td className="rowact"><button className="link" onClick={() => edit(r)}>Edit</button><button className="link danger" onClick={() => del(r.id)}>Delete</button></td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </section>
    </>
  );
}