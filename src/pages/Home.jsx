const SERVICES = [
  ['Expense and income tracking', 'Record what you spend and earn in a few seconds. Every amount is stored exactly, with no rounding drift.'],
  ['Receipt scanning', 'Upload a photo. We read the shop, date and total, and you check it before anything is saved.'],
  ['Daily, weekly and monthly budgets', 'Set a limit per category and see how much is left, or how far over you are.'],
  ['Reports', 'Spending by day, week, month and category, plus a comparison with the previous period.'],
  ['Unusual spending alerts', 'Expenses far above your normal range for a category are flagged for a second look.'],
  ['Spending forecast', 'A moving average of recent days gives an estimate of what comes next. It is an estimate, not a promise.'],
  ['AI saving advice', 'Ask why you went over budget. The AI explains figures we calculated; it never does the maths itself.'],
];

export default function Home({ onLogin, onRegister }) {
  return (
    <div className="home">
      <header className="home-top">
        <span className="brand-h">Budget Tracker</span>
        <div className="actions"><button className="btn ghost" onClick={onLogin}>Sign in</button><button className="btn" onClick={onRegister}>Get started</button></div>
      </header>

      <section className="hero">
        <div>
          <h1>Know where your baht goes before the month ends.</h1>
          <p className="lead">Track spending, set budgets and get clear, plain-language advice when you start to overspend.</p>
          <div className="actions"><button className="btn big" onClick={onRegister}>Create a free account</button><button className="btn ghost big" onClick={onLogin}>Sign in</button></div>
        </div>
        <div className="sample" aria-label="Example budget">
          <p className="muted">Daily food budget</p>
          <div className="sample-row"><span>Breakfast</span><b>฿50.00</b></div>
          <div className="sample-row"><span>Lunch</span><b>฿80.00</b></div>
          <div className="sample-row"><span>Dinner</span><b>฿90.00</b></div>
          <div className="meter"><i className="over" style={{ width: '100%' }} /></div>
          <div className="sample-row total"><span>฿220.00 of ฿150.00</span><b className="neg">฿70.00 over</b></div>
        </div>
      </section>

      <section className="services">
        <h2>What you can do</h2>
        <ul>{SERVICES.map(([t, d]) => <li key={t}><h3>{t}</h3><p>{d}</p></li>)}</ul>
      </section>

      <section className="steps">
        <h2>How it works</h2>
        <ol>
          <li><b>Add</b> your expenses and income, or scan a receipt.</li>
          <li><b>Set</b> a budget for the categories you care about.</li>
          <li><b>Review</b> your dashboard, alerts and advice.</li>
        </ol>
        <button className="btn big" onClick={onRegister}>Start tracking</button>
      </section>
      <footer className="home-foot">AI Budget Tracker, a university project.</footer>
    </div>
  );
}
