import { useState } from 'react';
import EmailSearchUI from './components/EmailSearchUI';
import HowItWorks from './components/HowItWorks';
import './App.css';

function App() {
  const [showDemo, setShowDemo] = useState(true);

  return (
    <div className="app-shell">
      <nav className="app-nav">
        <div className="app-nav__brand">Alokit_Onebox</div>
        <button className="app-nav__toggle" onClick={() => setShowDemo(!showDemo)}>
          {showDemo ? 'Hide Live Demo' : 'Try it Live'}
        </button>
      </nav>

      <header className="hero">
        <p className="hero__eyebrow">The AI-powered inbox companion</p>
        <h1>Revolutionize Your Inbox</h1>
        <p className="hero__subtitle">
          One unified workspace for searching, triaging, and understanding every email thread—without jumping between apps.
        </p>
        <div className="hero__benefits">
          <article>
            <h3>Morning triage</h3>
            <p>Skim alerts, investor notes, and product feedback in under five minutes.</p>
          </article>
          <article>
            <h3>Prep before meetings</h3>
            <p>Pull the last 10 touchpoints with a customer without digging through folders.</p>
          </article>
          <article>
            <h3>Never miss intent</h3>
            <p>Auto-highlight “interested” replies so your team responds before the competition.</p>
          </article>
        </div>
      </header>

      {showDemo && (
        <section className="demo">
          <EmailSearchUI />
        </section>
      )}

      <HowItWorks />
    </div>
  );
}

export default App;