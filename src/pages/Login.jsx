import { useState } from 'react';
import { api, token } from '../api.js';
import { Err } from '../components.jsx';

export default function Login({ mode, setMode, onBack, onDone }) {
  const [f, setF] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault(); setError(''); setBusy(true);
    try {
      if (mode === 'register') await api.register(f);
      const res = await api.login(f.username, f.password);
      token.set(res.access_token); token.setUser(f.username);
      onDone();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  return (
    <div className="login">
      <form className="panel login-card" onSubmit={submit}>
        <button type="button" className="link left" onClick={onBack}>Back to home</button>
        <h1>{mode === 'login' ? 'Sign in' : 'Create your account'}</h1>
        <label className="field"><span>Username</span><input value={f.username} onChange={set('username')} required autoComplete="username" /></label>
        {mode === 'register' && <label className="field"><span>Email</span><input type="email" value={f.email} onChange={set('email')} required /></label>}
        <label className="field"><span>Password</span><input type="password" value={f.password} onChange={set('password')} required minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
        <Err msg={error} />
        <button className="btn" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
        <button type="button" className="link" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>
          {mode === 'login' ? 'New here? Create an account' : 'Have an account? Sign in'}
        </button>
      </form>
    </div>
  );
}
