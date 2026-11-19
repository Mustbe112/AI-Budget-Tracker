const STEPS = [
  ['Capture', 'Add an expense or scan a receipt.'],
  ['Understand', 'See where your money goes.'],
  ['Set a plan', 'Build budgets around real life.'],
  ['Stay aware', 'Spot changes before they add up.'],
  ['Move forward', 'Make your next decision with clarity.'],
];

const OUTCOMES = [
  { mark: '01', title: 'A clearer picture', detail: 'See income and spending in one considered overview.' },
  { mark: '02', title: 'A plan that feels real', detail: 'Set flexible budgets around the categories that matter.' },
  { mark: '03', title: 'More confident choices', detail: 'Use plain-language insights to decide what comes next.' },
];

function AnimatedLine({ children, className = '' }) {
  return (
    <span className={className} aria-hidden="true">
      {[...children].map((letter, index) => (
        <span className="letter" key={`${letter}-${index}`} style={{ '--letter-index': index }}>
          {letter === ' ' ? '\u00a0' : letter}
        </span>
      ))}
    </span>
  );
}

export default function Home({ onLogin, onRegister }) {
  return (
    <main className="portfolio-page">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />
      <header className="portfolio-header">
        <a className="portfolio-brand" href="#top" aria-label="Budget Tracker home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>good<span className="brand-dot">.</span>budget</span>
        </a>
        <nav className="portfolio-nav" aria-label="Main navigation">
          <a href="#approach">Approach</a>
          <a href="#outcomes">Why it works</a>
        </nav>
        <div className="portfolio-actions">
          <button className="portfolio-signin" onClick={onLogin}>Sign in</button>
          <button className="portfolio-cta" onClick={onRegister}>Get started <span aria-hidden="true">↗</span></button>
        </div>
      </header>

      <section className="portfolio-hero" id="top">
        <div className="hero-orbit hero-orbit-one" aria-hidden="true" />
        <div className="hero-orbit hero-orbit-two" aria-hidden="true" />
        <p className="eyebrow hero-eyebrow"><span /> A calmer way to manage money</p>
        <h1 aria-label="Your money, in perspective.">
          <span className="title-line title-serif"><AnimatedLine>Your money,</AnimatedLine></span>
          <span className="title-line title-sans"><AnimatedLine>in perspective.</AnimatedLine></span>
        </h1>
        <span className="hero-rule" aria-hidden="true" />
        <p className="hero-description">A little more clarity in the everyday.<br />A lot more confidence in what comes next.</p>
        <div className="hero-actions">
          <button className="portfolio-cta portfolio-cta-large" onClick={onRegister}>Make a fresh start <span aria-hidden="true">↗</span></button>
          <a className="text-link" href="#approach">Get to know us <span aria-hidden="true">↓</span></a>
        </div>
        <div className="hero-note"><span className="note-star" aria-hidden="true">✳</span> Thoughtful tools for real-life finances</div>
      </section>

      <section className="preview-section" aria-label="Example monthly budget overview">
        <div className="preview-card">
          <div className="preview-top">
            <div><p className="eyebrow">A little perspective</p><h2>Your month, at a glance.</h2></div>
            <span className="preview-period">SAMPLE VIEW <span aria-hidden="true">↗</span></span>
          </div>
          <div className="preview-content">
            <div className="preview-balance">
              <span>Still in your plan</span>
              <strong>฿8,420<span>.00</span></strong>
              <div className="preview-progress"><i /></div>
              <small>68% of your monthly budget remains</small>
            </div>
            <div className="preview-chart" aria-label="Illustrative weekly spending chart">
              {[35, 58, 42, 76, 51, 88, 63].map((height, index) => (
                <div className={`chart-column${index === 5 ? ' chart-column-active' : ''}`} key={index}>
                  <i style={{ '--bar-height': `${height}%`, '--bar-index': index }} />
                  <span>{['M', 'T', 'W', 'T', 'F', 'S', 'S'][index]}</span>
                </div>
              ))}
            </div>
            <div className="preview-foot"><span><i /> On track this month</span><span>Every baht, in view</span></div>
          </div>
        </div>
        <span className="preview-caption">A simple place to begin again, every month.</span>
      </section>

      <section className="process-section" id="approach">
        <div className="section-heading">
          <div><p className="eyebrow">Small steps, meaningful change</p><h2>A process that makes<br /><em>room for real life.</em></h2></div>
          <p className="section-intro">No perfect budgets required. Just a clearer view of today, and a thoughtful next step.</p>
        </div>
        <div className="process-track">
          {STEPS.map(([title, detail], index) => (
            <article className="process-step" key={title}>
              <span className="step-number">{String(index + 1).padStart(2, '0')}</span>
              <div className="step-copy"><h3>{title}</h3><p>{detail}</p></div>
            </article>
          ))}
        </div>
      </section>

      <section className="outcomes-section" id="outcomes">
        <div className="outcomes-title">
          <p className="eyebrow">The difference is in the details</p>
          <h2>Money management,<br /><em>with a human touch.</em></h2>
          <p>Everything you need to feel informed, not overwhelmed.</p>
        </div>
        <div className="outcome-list">
          {OUTCOMES.map(({ mark, title, detail }) => (
            <article className="outcome-item" key={mark}>
              <span className="outcome-mark">{mark}</span>
              <div><h3>{title}</h3><p>{detail}</p></div>
              <span className="outcome-arrow" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
      </section>

      <section className="closing-section">
        <p className="eyebrow">Your next chapter starts here</p>
        <h2>Feel good about<br /><em>where you’re going.</em></h2>
        <button className="portfolio-cta portfolio-cta-large" onClick={onRegister}>Let’s get started <span aria-hidden="true">↗</span></button>
      </section>

      <footer className="portfolio-footer">
        <a className="portfolio-brand" href="#top">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>good<span className="brand-dot">.</span>budget</span>
        </a>
        <span>Made for the life you’re living.</span>
        <button className="footer-login" onClick={onLogin}>Already with us? Sign in <span aria-hidden="true">↗</span></button>
      </footer>
    </main>
  );
}
