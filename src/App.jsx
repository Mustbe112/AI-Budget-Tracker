import { useEffect, useState } from 'react';
import { token } from './api.js';
import Home from './pages/Home.jsx';
import Login from './pages/Login.jsx';
import Profile from './pages/Profile.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Resource from './pages/Resource.jsx';
import Reports from './pages/Reports.jsx';
import Analysis from './pages/Analysis.jsx';
import Receipts from './pages/Receipts.jsx';
import Assistant from './pages/Assistant.jsx';

const CATEGORIES = ['food', 'transport', 'shopping', 'bills', 'health', 'entertainment', 'education', 'other'];

const EXPENSE = {
  title: 'Expenses', path: '/expenses', filters: ['category'],
  fields: [
    { name: 'amount', label: 'Amount (฿)', type: 'number', required: true },
    { name: 'category', label: 'Category', options: CATEGORIES, required: true },
    { name: 'merchant', label: 'Merchant' },
    { name: 'description', label: 'Description' },
    { name: 'expense_date', label: 'Date', type: 'date', required: true },
  ],
  cols: ['expense_date', 'category', 'merchant', 'description', 'amount'],
};
const INCOME = {
  title: 'Income', path: '/income',
  fields: [
    { name: 'amount', label: 'Amount (฿)', type: 'number', required: true },
    { name: 'source', label: 'Source', required: true },
    { name: 'date', label: 'Date', type: 'date', required: true },
  ],
  cols: ['date', 'source', 'amount'],
};
const BUDGET = {
  title: 'Budgets', path: '/budgets', showCheck: true,
  fields: [
    { name: 'category', label: 'Category', options: CATEGORIES, required: true },
    { name: 'amount', label: 'Budget (฿)', type: 'number', required: true },
    { name: 'period', label: 'Period', options: ['daily', 'weekly', 'monthly'], required: true },
    { name: 'start_date', label: 'Start', type: 'date', required: true },
    { name: 'end_date', label: 'End', type: 'date' },
  ],
  cols: ['category', 'period', 'amount', 'start_date', 'end_date'],
};

const NAV = [
  ['dashboard', 'Overview'], ['expenses', 'Expenses'], ['income', 'Income'], ['budgets', 'Budgets'],
  ['receipts', 'Scan receipt'], ['reports', 'Reports'], ['analysis', 'Analysis'], ['assistant', 'Assistant'],
];

export default function App() {
  const [authed, setAuthed] = useState(!!token.get());
  const [page, setPage] = useState('dashboard');
  const [pre, setPre] = useState('home'); // home | login | register

  useEffect(() => {
    const out = () => setAuthed(false);
    window.addEventListener('abt-logout', out);
    return () => window.removeEventListener('abt-logout', out);
  }, []);

  const signOut = () => { token.clear(); setAuthed(false); setPre('home'); setPage('dashboard'); };
  if (!authed) {
    if (pre === 'home') return <Home onLogin={() => setPre('login')} onRegister={() => setPre('register')} />;
    return <Login mode={pre} setMode={setPre} onBack={() => setPre('home')} onDone={() => setAuthed(true)} />;
  }

  const views = {
    dashboard: <Dashboard go={setPage} />,
    expenses: <Resource {...EXPENSE} />,
    income: <Resource {...INCOME} />,
    budgets: <Resource {...BUDGET} />,
    receipts: <Receipts categories={CATEGORIES} onSaved={() => setPage('expenses')} />,
    reports: <Reports />,
    analysis: <Analysis />,
    assistant: <Assistant />,
    profile: <Profile onSignOut={signOut} />,
  };

  return (
    <div className="shell">
      <nav className="side">
        <div className="brand">Budget<br />Tracker</div>
        {NAV.map(([id, label]) => (
          <button key={id} className={page === id ? 'nav on' : 'nav'} onClick={() => setPage(id)}>{label}</button>
        ))}
        <button className={page === 'profile' ? 'nav out on' : 'nav out'} onClick={() => setPage('profile')}>Profile{token.user() ? ` (${token.user()})` : ''}</button>
        <button className="nav" onClick={signOut}>Sign out</button>
      </nav>
      <main className="main" key={page}>{views[page]}</main>
    </div>
  );
}
