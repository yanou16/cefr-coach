import { useState } from 'react'
import { api } from '../api/client'

interface Props {
  onStart: () => void
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

const LEVELS = [
  { code: 'A1', name: 'Beginner',     desc: 'Basic phrases, greetings, simple introductions' },
  { code: 'A2', name: 'Elementary',   desc: 'Everyday topics, simple texts, short conversations' },
  { code: 'B1', name: 'Intermediate', desc: 'Main ideas, travel, work and study situations' },
  { code: 'B2', name: 'Upper-Inter.', desc: 'Complex texts, debate, native-speaker exchanges' },
  { code: 'C1', name: 'Advanced',     desc: 'Fluent, spontaneous, academic and professional' },
  { code: 'C2', name: 'Mastery',      desc: 'Near-native precision, nuance, register control' },
] as const

const LEVEL_NAMES: Record<string, string> = {
  A1: 'Beginner', A2: 'Elementary', B1: 'Intermediate',
  B2: 'Upper-Intermediate', C1: 'Advanced', C2: 'Mastery',
}

const EXAMPLES = [
  {
    level: 'A2',
    label: 'Elementary',
    text: 'Yesterday I go to market with my friend. We buyed food and some clothes. I like go shopping every weekend because is fun and I can see many peoples.',
    signals: ['verb tense errors', 'missing articles', 'simple vocabulary'],
  },
  {
    level: 'B1',
    label: 'Intermediate',
    text: "I've been working at this company for two years now. Although the job can be stressful sometimes, I really enjoy working with the team and having opportunities to develop new professional skills.",
    signals: ['present perfect correct', 'compound sentences', 'hedging language'],
  },
  {
    level: 'C1',
    label: 'Advanced',
    text: 'The unprecedented proliferation of algorithmic content curation has fundamentally reshaped the information landscape, raising profound questions about epistemic autonomy and the nature of public discourse in democratic societies.',
    signals: ['nominalisation', 'embedded clauses', 'academic register'],
  },
] as const

export default function LandingPage({ onStart, theme, toggleTheme }: Props) {
  const [demoText, setDemoText]       = useState('')
  const [demoResult, setDemoResult]   = useState<{ level: string; confidence: number } | null>(null)
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoError, setDemoError]     = useState(false)

  const wordCount = demoText.trim() === '' ? 0 : demoText.trim().split(/\s+/).length
  const demoReady = wordCount >= 15 && !demoLoading

  async function runDemo() {
    if (!demoReady) return
    setDemoLoading(true)
    setDemoResult(null)
    setDemoError(false)
    try {
      const sessionId = `demo-${Date.now()}`
      const res = await api.classifySession(demoText, sessionId)
      setDemoResult({ level: res.level ?? '', confidence: res.confidence ?? 0 })
    } catch {
      setDemoError(true)
    } finally {
      setDemoLoading(false)
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && e.metaKey) runDemo()
  }

  return (
    <div className="lp-root">

      {/* ── Nav ───────────────────────────────────────────── */}
      <nav className="lp-nav">
        <div className="lp-logo">CEFR <em>Coach</em></div>
        <div className="lp-nav-right">
          <span className="lp-nav-tag">Build Week 2026</span>
          <button className="theme-btn" onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
            {theme === 'dark' ? '☀' : '☽'}
          </button>
          <button className="lp-nav-cta" onClick={onStart}>Try it free →</button>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────── */}
      <section className="lp-hero">
        <div className="lp-hero-left">
          <p className="lp-eyebrow">
            <span className="lp-eyebrow-line" />
            Adaptive English tutor · A1 → C2
          </p>
          <h1 className="lp-h1">
            Your English,<br /><em>precisely</em><br />calibrated.
          </h1>
          <p className="lp-sub">
            Write two short samples. The AI reads your grammar in seconds,
            pins your CEFR level, and gives you exercises exactly one step
            ahead of where you stand. No placement test. No setup.
          </p>
          <div className="lp-actions">
            <button className="lp-btn-main" onClick={onStart}>
              Start your session →
            </button>
            <span className="lp-note">Free · No account needed</span>
          </div>
        </div>

        <div className="lp-hero-right">
          <div className="lp-demo-wrap">
            <div className="lp-demo-detected">✦ Detected: B1 Intermediate</div>
            <div className="lp-demo-card">
              <div className="lp-d-watermark">B1</div>
              <div className="lp-d-head">
                <span className="lp-d-tag">Fill in the blank</span>
                <span className="lp-d-skill">conditional</span>
                <span className="lp-d-lvl">B1</span>
              </div>
              <p className="lp-d-instr">Complete with the correct verb form.</p>
              <div className="lp-d-text">
                If she <span className="lp-blank" data-n="(1)" /> harder last
                year, she <span className="lp-blank" data-n="(2)" /> the exam.
              </div>
              <div className="lp-d-answer">had studied… would have passed</div>
              <div className="lp-d-fb">
                <div className="lp-d-score">88</div>
                <div className="lp-d-fb-body">
                  <strong>Correct third conditional</strong>
                  Both verbs perfectly formed. Notice the past perfect in the if-clause.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Credibility strip ─────────────────────────────── */}
      <div className="lp-cred-strip">
        <div className="lp-cred-inner">
          <div className="lp-cred-item"><em>84.9%</em> classifier accuracy</div>
          <span className="lp-cred-dot" />
          <div className="lp-cred-item"><em>6</em> CEFR levels</div>
          <span className="lp-cred-dot" />
          <div className="lp-cred-item"><em>82</em> corpus chunks</div>
          <span className="lp-cred-dot" />
          <div className="lp-cred-item">Krashen <em>i+1</em> method</div>
          <span className="lp-cred-dot" />
          <div className="lp-cred-item"><em>QLoRA</em> fine-tuned classifier</div>
          <span className="lp-cred-dot" />
          <div className="lp-cred-item">OpenAI <em>GPT-5.6</em> feedback</div>
        </div>
      </div>

      {/* ── Mini-demo ─────────────────────────────────────── */}
      <div className="lp-try-wrap">
        <div className="lp-try-inner">
          <div className="lp-try-header">
            <p className="lp-s-eyebrow">Live classifier · No setup</p>
            <h2 className="lp-s-title">Detect your level right now.</h2>
            <p className="lp-try-sub">
              Write anything in English — a few sentences about your day, your job, your hobbies.
              The AI will classify your CEFR level instantly.
            </p>
          </div>

          <div className="lp-try-card">
            <textarea
              className="lp-try-ta"
              value={demoText}
              onChange={e => { setDemoText(e.target.value); setDemoResult(null); setDemoError(false) }}
              onKeyDown={handleKey}
              placeholder="Write a few sentences in English… (min. 15 words)"
              rows={5}
            />
            <div className="lp-try-footer">
              <span className={`lp-try-wc${wordCount >= 15 ? ' lp-try-wc--ok' : ''}`}>
                {wordCount} / 15 words
              </span>
              <button
                className="lp-btn-main lp-try-btn"
                onClick={runDemo}
                disabled={!demoReady}
              >
                {demoLoading ? 'Classifying…' : 'Detect my level →'}
              </button>
            </div>
          </div>

          {/* Result */}
          {demoResult && (
            <div className="lp-try-result" key={demoResult.level}>
              <div
                className="lp-try-badge"
                style={{
                  background: `var(--lvl-${demoResult.level.toLowerCase()})`,
                  color: `var(--lvl-${demoResult.level.toLowerCase()}-fg)`,
                }}
              >
                {demoResult.level}
              </div>
              <div className="lp-try-result-info">
                <p className="lp-try-result-level">
                  {LEVEL_NAMES[demoResult.level] ?? demoResult.level}
                </p>
                <p className="lp-try-result-conf">
                  {Math.round(demoResult.confidence * 100)}% confidence
                </p>
              </div>
              <button className="lp-btn-main lp-try-cta" onClick={onStart}>
                Practice at {demoResult.level} →
              </button>
            </div>
          )}

          {demoError && (
            <p className="lp-try-err">
              Classifier unavailable — the full app works the same way.{' '}
              <button className="lp-try-err-btn" onClick={onStart}>Start anyway →</button>
            </p>
          )}
        </div>
      </div>

      {/* ── Example texts ─────────────────────────────────── */}
      <div className="lp-examples-wrap">
        <div className="lp-examples-inner">
          <p className="lp-s-eyebrow">See it in action</p>
          <h2 className="lp-s-title">What each level looks like.</h2>
          <div className="lp-examples">
            {EXAMPLES.map(ex => (
              <div key={ex.level} className="lp-ex-card">
                <div
                  className="lp-ex-badge"
                  style={{
                    background: `var(--lvl-${ex.level.toLowerCase()})`,
                    color: `var(--lvl-${ex.level.toLowerCase()}-fg)`,
                  }}
                >
                  <span className="lp-ex-code">{ex.level}</span>
                  <span className="lp-ex-name">{ex.label}</span>
                </div>
                <p className="lp-ex-text">"{ex.text}"</p>
                <ul className="lp-ex-signals">
                  {ex.signals.map(s => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Spectrum ──────────────────────────────────────── */}
      <div className="lp-spectrum-wrap">
        <div className="lp-spectrum-inner">
          <p className="lp-s-eyebrow">Six levels · One clear path</p>
          <h2 className="lp-s-title">Where are you on the spectrum?</h2>
          <div className="lp-spectrum">
            {LEVELS.map(l => (
              <div key={l.code} className="lp-seg"
                style={{
                  background: `var(--lvl-${l.code.toLowerCase()})`,
                  color:      `var(--lvl-${l.code.toLowerCase()}-fg)`,
                }}>
                <span className="lp-seg-code">{l.code}</span>
                <span className="lp-seg-name">{l.name}</span>
                <span className="lp-seg-desc">{l.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── How it works ──────────────────────────────────── */}
      <div className="lp-how-wrap">
        <div className="lp-how-header">
          <p className="lp-s-eyebrow">The adaptive loop</p>
          <h2 className="lp-s-title">How it works.</h2>
        </div>
        <div className="lp-steps">
          <div className="lp-step">
            <p className="lp-step-n">01 — Write</p>
            <div className="lp-step-mark lp-step-mark--w">W</div>
            <h3 className="lp-step-h">Show, don't tell</h3>
            <p className="lp-step-p">
              Write two short samples on any topic. The fine-tuned classifier
              reads your grammar and vocabulary to pinpoint your exact CEFR
              level — no self-assessment needed.
            </p>
          </div>
          <div className="lp-step">
            <p className="lp-step-n">02 — Practice</p>
            <div className="lp-step-mark lp-step-mark--i">i+1</div>
            <h3 className="lp-step-h">The challenge zone</h3>
            <p className="lp-step-p">
              Every exercise targets the level just above yours — Krashen's i+1.
              Grammar, vocabulary, writing tasks pulled from a RAG corpus
              matched to your exact gap.
            </p>
          </div>
          <div className="lp-step">
            <p className="lp-step-n">03 — Level up</p>
            <div className="lp-step-mark lp-step-mark--u">↑</div>
            <h3 className="lp-step-h">Classifier-driven</h3>
            <p className="lp-step-p">
              Your level updates from what you write — not points or streaks.
              Consistent strong answers move you up; the system catches when
              you need more time at a level.
            </p>
          </div>
        </div>
      </div>

      {/* ── CTA ───────────────────────────────────────────── */}
      <div className="lp-cta-wrap">
        <div className="lp-cta-left">
          <h2 className="lp-cta-h">Find your level.<br />Then raise it.</h2>
          <p className="lp-cta-sub">
            Takes 2 minutes to classify. Works from A1 beginner to C2 near-native.
          </p>
        </div>
        <div className="lp-cta-right">
          <button className="lp-btn-main" onClick={onStart}>
            Start your session →
          </button>
        </div>
      </div>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className="lp-footer">
        <span>CEFR Coach · Build Week 2026</span>
        <span>QLoRA CEFR classifier · Krashen i+1 · ChromaDB RAG · OpenAI GPT-5.6</span>
      </footer>

    </div>
  )
}
