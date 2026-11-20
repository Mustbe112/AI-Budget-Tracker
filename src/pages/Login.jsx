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
    <main className="login">
      <div className="auth-orb auth-orb-one" aria-hidden="true" />
      <div className="auth-orb auth-orb-two" aria-hidden="true" />
      <header className="auth-header">
        <a className="portfolio-brand" href="/" onClick={(e) => { e.preventDefault(); onBack(); }}>
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>good<span className="brand-dot">.</span>budget</span>
        </a>
        <button type="button" className="auth-back" onClick={onBack}><span aria-hidden="true">←</span> Back to home</button>
      </header>
      <div className="auth-layout">
        <section className="auth-story">
          <p className="eyebrow"><span /> A little more clarity</p>
          <h1>Feel good about<br /><em>where you’re going.</em></h1>
          <p>Small, thoughtful steps toward a healthier relationship with money.</p>
          <span className="auth-story-rule" />
          <span className="auth-story-note">YOUR MONEY, IN PERSPECTIVE.</span>
        </section>
        <form className="panel login-card" onSubmit={submit}>
          <p className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'A FRESH START'}</p>
          <h2>{mode === 'login' ? 'Sign in' : 'Create your account'}</h2>
          <p className="auth-intro">{mode === 'login' ? 'Pick up where you left off.' : 'Your next chapter starts here.'}</p>
          <label className="field"><span>Username</span><input value={f.username} onChange={set('username')} required autoComplete="username" /></label>
          {mode === 'register' && <label className="field"><span>Email</span><input type="email" value={f.email} onChange={set('email')} required /></label>}
          <label className="field"><span>Password</span><input type="password" value={f.password} onChange={set('password')} required minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
          <Err msg={error} />
          <button className="btn" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}<span aria-hidden="true">↗</span></button>
          <button type="button" className="link" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>
            {mode === 'login' ? 'New here? Create an account' : 'Have an account? Sign in'}
          </button>
        </form>
      </div>
    </main>
  );
}
