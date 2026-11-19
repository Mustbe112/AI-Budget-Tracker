import { useEffect, useState } from 'react';
import { api, token } from '../api.js';
import { Err } from '../components.jsx';

export default function Profile({ onSignOut }) {
  const [me, setMe] = useState(null);
  const [f, setF] = useState({ username: '', email: '' });
  const [pw, setPw] = useState({ current_password: '', new_password: '' });
  const [msg, setMsg] = useState({ profile: '', pw: '' });
  const [err, setErr] = useState({ load: '', profile: '', pw: '' });

  useEffect(() => {
    api.me().then((u) => { setMe(u); setF({ username: u.username || '', email: u.email || '' }); })
      .catch((e) => setErr((s) => ({ ...s, load: e.message })));
  }, []);

  const saveProfile = async (e) => {
    e.preventDefault(); setErr((s) => ({ ...s, profile: '' })); setMsg((s) => ({ ...s, profile: '' }));
    try { const u = await api.updateMe(f); setMe(u); token.setUser(u.username || f.username); setMsg((s) => ({ ...s, profile: 'Profile saved.' })); }
    catch (x) { setErr((s) => ({ ...s, profile: x.message })); }
  };
  const savePw = async (e) => {
    e.preventDefault(); setErr((s) => ({ ...s, pw: '' })); setMsg((s) => ({ ...s, pw: '' }));
    try { await api.changePassword(pw); setPw({ current_password: '', new_password: '' }); setMsg((s) => ({ ...s, pw: 'Password changed.' })); }
    catch (x) { setErr((s) => ({ ...s, pw: x.message })); }
  };

  const name = me?.username || token.user() || 'You';
  const joined = me?.created_at || me?.created_date;

  return (
    <>
      <h1>Profile</h1>
      <Err msg={err.load} />
      <section className="panel profile-head">
        <div className="avatar" aria-hidden>{name[0]?.toUpperCase()}</div>
        <div><h2>{name}</h2><p className="muted" style={{ margin: 0 }}>{me?.email}{joined ? ` · Member since ${new Date(joined).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}` : ''}</p></div>
      </section>
      <form className="panel grid" onSubmit={saveProfile}>
        <h2 className="span">Account details</h2>
        <label className="field"><span>Username</span><input value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} required /></label>
        <label className="field"><span>Email</span><input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required /></label>
        <div className="actions span"><button className="btn">Save changes</button></div>
        <Err msg={err.profile} />{msg.profile && <p className="ok span">{msg.profile}</p>}
      </form>
      <form className="panel grid" onSubmit={savePw}>
        <h2 className="span">Change password</h2>
        <label className="field"><span>Current password</span><input type="password" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} required autoComplete="current-password" /></label>
        <label className="field"><span>New password</span><input type="password" minLength={8} value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} required autoComplete="new-password" /></label>
        <div className="actions span"><button className="btn">Update password</button></div>
        <Err msg={err.pw} />{msg.pw && <p className="ok span">{msg.pw}</p>}
      </form>
      <button className="btn ghost" onClick={onSignOut}>Sign out</button>
    </>
  );
}
