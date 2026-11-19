import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Err, SmartView, useAsync } from '../components.jsx';

const KINDS = ['daily', 'weekly', 'monthly', 'categories', 'comparison'];

export default function Reports() {
  const [kind, setKind] = useState('daily');
  const [p, setP] = useState({ date: '', start_date: '', end_date: '' });
  const [{ loading, error, data }, run] = useAsync();
  useEffect(() => { run(() => api.report(kind, p)); /* eslint-disable-next-line */ }, [kind]);

  return (
    <>
      <h1>Reports</h1>
      <div className="tabs">{KINDS.map((k) => <button key={k} className={k === kind ? 'tab on' : 'tab'} onClick={() => setKind(k)}>{k}</button>)}</div>
      <form className="panel grid" onSubmit={(e) => { e.preventDefault(); run(() => api.report(kind, p)); }}>
        {['date', 'start_date', 'end_date'].map((k) => (
          <label key={k} className="field"><span>{k.replace('_', ' ')}</span><input type="date" value={p[k]} onChange={(e) => setP({ ...p, [k]: e.target.value })} /></label>
        ))}
        <div className="actions"><button className="btn">Update report</button></div>
      </form>
      <Err msg={error} />
      {loading ? <p className="muted">Loading…</p> : <SmartView data={data} />}
    </>
  );
}
