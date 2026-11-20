import { useState } from 'react';
import { api } from '../api.js';
import { DataView, Err, useAsync } from '../components.jsx';

// Backend replies look like { text, ai_generated, provider, disclaimer, facts }.
// Pull out the readable text; never dump the whole object into the UI.
const textOf = (r) => {
  if (typeof r === 'string') return r;
  const t = r?.text ?? r?.answer ?? r?.response ?? r?.recommendations ?? r?.message;
  return typeof t === 'string' ? t : null;
};

export default function Assistant() {
  const [q, setQ] = useState('');
  const [chat, setChat] = useState([]);
  const [chatErr, setChatErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [{ loading, error, data }, run] = useAsync();

  const ask = async (e) => {
    e.preventDefault();
    const question = q.trim(); if (!question) return;
    setQ(''); setChatErr(''); setBusy(true);
    setChat((c) => [...c, { who: 'you', text: question }]);
    try {
      const r = await api.aiChat(question);
      setChat((c) => [...c, { who: 'ai', text: textOf(r) ?? 'Sorry, I could not read the answer.', disclaimer: r?.disclaimer }]);
    } catch (err) { setChatErr(err.message); } finally { setBusy(false); }
  };

  const recText = data ? textOf(data) : null;

  return (
    <>
      <h1>Assistant</h1>
      <p className="note">Amounts come from your saved records. The AI only explains them. If the AI service is offline, the rest of the app still works.</p>
      <section className="panel">
        <div className="bar"><h2>Saving recommendations</h2><button className="btn" onClick={() => run(() => api.aiRecommend())} disabled={loading}>{loading ? 'Thinking…' : 'Get recommendations'}</button></div>
        <Err msg={error} />
        {data && (recText
          ? <><p className="prose" style={{ whiteSpace: 'pre-wrap' }}>{recText}</p>{data.disclaimer && <small className="muted">{data.disclaimer}</small>}</>
          : <DataView data={data} />)}
      </section>
      <section className="panel">
        <h2>Ask about your spending</h2>
        <div className="chat">
          {!chat.length && <p className="muted">Try: “Why did I go over my food budget this week?”</p>}
          {chat.map((m, i) => (
            <div key={i} className={`bubble ${m.who}`}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
              {m.disclaimer && <small className="muted" style={{ display: 'block', marginTop: '.5rem' }}>{m.disclaimer}</small>}
            </div>
          ))}
          {busy && <p className="bubble ai muted">Thinking…</p>}
        </div>
        <Err msg={chatErr} />
        <form className="ask" onSubmit={ask}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question" aria-label="Question" />
          <button className="btn" disabled={busy}>Send</button>
        </form>
      </section>
    </>
  );
}