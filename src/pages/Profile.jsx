import { useEffect, useState } from 'react';
import { api, token } from '../api.js';
import { Err } from '../components.jsx';

// The backend currently only has GET /auth/me, so the profile is read-only.
export default function Profile({ onSignOut }) {
  const [me, setMe] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { api.me().then(setMe).catch((e) => setError(e.message)); }, []);

  const name = me?.username || token.user() || 'You';
  const rows = me ? [
    ['Username', me.username],
    ['Email', me.email],
    ['Member since', me.created_at ? new Date(me.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'],
    ['User ID', me.id],
  ] : [];

  return (
    <>
      <h1>Profile</h1>
      <Err msg={error} />
      <section className="panel profile-head">
        <div className="avatar" aria-hidden>{name[0]?.toUpperCase()}</div>
        <div><h2>{name}</h2><p className="muted" style={{ margin: 0 }}>{me?.email}</p></div>
      </section>
      <section className="panel">
        <h2>Account details</h2>
        <dl className="kv">{rows.map(([k, v]) => <div key={k} className="kv-row"><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
        <p className="note" style={{ marginTop: '1rem' }}>Editing your details and changing your password are not available yet.</p>
      </section>
      <button className="btn ghost" onClick={onSignOut}>Sign out</button>
    </>
  );
}